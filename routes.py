from difflib import SequenceMatcher
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()
import sqlite3
from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    request,
    session,
    jsonify
)
import base64
import urllib.request
from werkzeug.utils import secure_filename
from io import BytesIO
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy 
import datetime
import os
from ocr import ocr_drug
# from paddleocr import PaddleOCR,draw_ocr
from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError
from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
from app import create_app, db, login_manager,bcrypt
from models import User, Note
from forms import login_form,register_form
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from function import create_note, delete_note, update_note, read_notes 

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = create_app()
# ocr = PaddleOCR(use_angle_cls=True, lang='en')
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    # render_template('index2.html')
    return render_template('index.html')

@app.route("/predict", methods=['POST'])
def predict():
    conn = sqlite3.connect('database.db')
    cursor = conn.execute(f"SELECT text from note WHERE username_id = {current_user.id}")
    allergy_list = [] #TODO: allergy_list
    for row in cursor:
        allergy_list.append(row[0])
    conn.close()
    if 'files[]' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    files = request.files.getlist('files[]')
    errors = {}
    success = False
    
    allergy_result = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            encoded_image = base64.b64encode(file.read())
            decoded_image = base64.b64decode(encoded_image)
            
            ocr_result = ocr_drug(decoded_image) #, cls = True)
            for i in range(len(ocr_result)):
                ingredient = ocr_result[i][1][0].lower()
                allergy_status = 'Safe'
                for element in allergy_list:
                    score = similar(ingredient, element)
                    if score >= 0.7:
                        allergy_status = 'Allergy'
                        break
                allergy_result.append([ingredient, allergy_status, str(encoded_image)])
                        
            success = True
        else: 
            errors[file.filename] = 'File type is not allowed'
    if success:
        resp = jsonify({'drug_list': allergy_result})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify(errors)
        resp.status_code = 400
        return resp

@app.route('/camera', methods=['POST','GET'])
def camera():
    return render_template('camera.html')

@app.route('/captured', methods=['POST'])
def captured():
    conn = sqlite3.connect('database.db')
    cursor = conn.execute(f"SELECT text from note WHERE username_id = {current_user.id}")
    allergy_list = []
    allergy_result = []
    for row in cursor:
        allergy_list.append(row[0])
    conn.close()
    data = request.get_json()
    image = base64.b64decode(data.split(",")[1])
    result = ocr_drug(image) #, cls=True)
    for i in range(len(result)):
        ingredient = result[i][1][0].lower()
        allergy_status = 'Safe'
        for element in allergy_list:
            score = similar(ingredient, element)
            if score >= 0.6:
                allergy_status = 'Allergy'
                break
        allergy_result.append([ingredient, allergy_status])
    
    resp = jsonify({'message' : allergy_result})
    return resp

@app.route("/list", methods=["POST", "GET"])
def listed():
    if request.method == "POST":
        data = request.get_json()
        if data.split(" ")[0] == 'add':
            create_note(data[3:])
        elif data.split(" ")[0]== 'delete':
            delete_note(data[7:])
        database = Note.query.all()
    return render_template("todolist.html", database = read_notes())

# @app.route("/edit/<note_id>", methods=["POST", "GET"])
# def edit_note(note_id):
#     if request.method == "POST":
#         update_note(note_id, text=request.form['text'], done=request.form['done'])
#     elif request.method == "GET":
#         delete_note(note_id)
#     return redirect("/ingredient", code=302)


@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )

# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
            db.session.add(newuser)
            db.session.commit()

            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
