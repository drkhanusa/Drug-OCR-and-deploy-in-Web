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
import sys
sys.path.insert(1, '/projects/khanhnt/PaddleOCR')
from paddleocr import PaddleOCR,draw_ocr
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
from app import create_app,db,login_manager,bcrypt
from models import User
from forms import login_form,register_form

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app = create_app()
ocr = PaddleOCR(use_angle_cls=True, lang='en')
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
    if 'files[]' not in request.files:
        resp = jsonify({'message' : 'No file part in the request'})
        resp.status_code = 400
        return resp
    files = request.files.getlist('files[]')
    errors = {}
    success = False
    line = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            encoded_image = base64.b64encode(file.read())
            decoded_image = base64.b64decode(encoded_image)
            result = ocr.ocr(decoded_image, cls = True)
            for i in range(len(result)):
                line.append(result[i][1][0])
            success = True
        else: 
            errors[file.filename] = 'File type is not allowed'
    if success and errors:
        errors['message'] = 'File(s) successfully uploaded'
        resp = jsonify(errors)
        resp.status_code = 206
        return resp
    if success:
        resp = jsonify({'message': line})
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
	line = []
	data = request.get_json()
	image = base64.b64decode(data.split(",")[1])
	result = ocr.ocr(image, cls=True)
	for i in range(len(result)):
		line.append(result[i][1][0])
	resp = jsonify({'message' : line})
	return resp

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
