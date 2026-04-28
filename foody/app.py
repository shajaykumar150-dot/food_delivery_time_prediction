from flask import Flask,render_template,redirect,request,url_for,session,flash
import mysql.connector
from werkzeug.security import generate_password_hash,check_password_hash
import re
import joblib
import numpy as np
import pandas as pd



app=Flask(__name__)
app.secret_key='1122'

model=joblib.load("model.pkl")
lb=joblib.load("traffic_encoder.pkl")
x=joblib.load("model_coloumns.pkl")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="food_db",
        port="3307"
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/methodology')
def methodology():
    return render_template('methodology.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']

        #Basic validation
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$",email):
            flash("Invalid email address","danager")
            return redirect(url_for('login'))
        
        if len(password)<6:
            flash("Password is Incorrect","danger")
            return redirect(url_for('login'))
        
        conn=get_db_connection()
        cursor=conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
        user=cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'],password):
            session['user_id']=user['u_id']
            session['username']=user['uname']
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password","danger")
            return redirect(url_for('login'))



    return render_template('login.html')

    

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['uname']
        email=request.form['email']
        password=request.form['password']

        #Basic validation
        if not name.strip():
            flash('username is required',"danger")
            return redirect(url_for('register'))
        
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            flash('invalid email address',"danger")
            return redirect(url_for('register'))
        
        if len(password)<6:
            flash('password must be at least 6 characters',"danger")
            return redirect(url_for('register'))
        
        hashed_password=generate_password_hash(password)
    
        conn=get_db_connection()
        cursor=conn.cursor()

        #check for the existing email
        cursor.execute("SELECT u_id FROM users WHERE email=%s",(email,))
        if cursor.fetchone():
            flash("email already exists","danger")
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        #INSERT USER
        cursor.execute(
            "INSERT INTO users (uname,email,password) VALUES (%s,%s,%s)",
            (name,email,hashed_password)
        )
        conn.commit()

        cursor.close()

        conn.close()

        flash("Registration Successful.Please Login","success")
        return redirect(url_for('login'))
        


    return render_template("register.html")

@app.route('/predict',methods=['GET','POST'])
def predict():

    if 'user_id' not in session:
        flash("Please Logint to access the prediction Page","warning")
        return redirect(url_for('login'))
    
    prediction=None
    
    if request.method=='POST':
        distance_km=int(request.form['distance_km'])
        traffic_level=int(request.form['traffic_level'])
        preparation_time_min=int(request.form['preparation_time_min'])
        courier_experience_yrs=int(request.form['courier_experience_yrs'])
        weather=request.form['weather']
        time_of_day=request.form['time_of_day']
        vehicle=request.form['vehicle']

        input_dict = {
        "distance_km": distance_km,
        "traffic_level": traffic_level,
        "preparation_time_min": preparation_time_min,
        "courier_experience_yrs": courier_experience_yrs,


        "weather_Foggy":1 if weather=="Foggy" else 0,
        "weather_Rainy":1 if weather=="Rainy" else 0,
        "weather_Snowy":1 if weather=="Snowy" else 0,
        "weather_Windy":1 if weather=="Windy" else 0,

        "time_of_day_Evening":1 if time_of_day=="Evening" else 0,
        "time_of_day_Morning" :1 if time_of_day=="Morning" else 0,        
        "time_of_day_Night":1 if time_of_day=="Night" else 0,

        "vehicle_type_Car": 1 if vehicle == "Car" else 0,
            "vehicle_type_Scooter": 1 if vehicle == "Scooter" else 0
        }

        input_df=pd.DataFrame([input_dict])
        input_df=input_df.reindex(columns=x,fill_value=0)

        prediction_model=model.predict(input_df)

        prediction=f"predicted deliver time{prediction_model[0]:.2f}minutes"


    

    return render_template('predict.html',prediction=prediction)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True,port=4000)