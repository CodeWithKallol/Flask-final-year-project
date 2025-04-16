from flask import Flask,  render_template, request, redirect, url_for, session, json, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cv2

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress a warning
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#Student Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    roll_no = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_pic = db.Column(db.String(), nullable=True) # Removed LargeBinary

    def __repr__(self):
        return f"Student(Name='{self.name}', Roll No='{self.roll_no}', Email='{self.email}', ProfilePic='{self.profile_pic}')"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#Teacher Model
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    #profile_pic = db.Column(db.LargeBinary) # Removed LargeBinary

    def __repr__(self):
        return f"Teacher(Name='{self.name}', Email='{self.email}')"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

with app.app_context():
    db.create_all()

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/studentOrteacher', methods =['GET', 'POST'])
def selectregister():
    if request.method == 'POST':
        if 'studentRegister' in request.form:
            return redirect(url_for('student_Reg'))
        elif 'teacherRegister' in request.form:
            return redirect(url_for('teacher_Reg'))
    return render_template('registerPage.html')



@app.route('/studentRegister', methods=['GET', 'POST'])
def student_Reg():
    if request.method == 'POST':
        name = request.form.get('name')
        semester = int(request.form.get('choice'))  # Corrected variable name to semester
        roll_no = request.form.get('rollNo')
        email = request.form.get('emailAdd')
        password = request.form.get('password')
        profile_pic = request.form['pic']
        
        
        if not name or not semester or not roll_no or not email or not password:
            return "All fields are required", 400

        # Check if email or roll number already exists
        existing_student = Student.query.filter_by(email=email).first()
        existing_rollno = Student.query.filter_by(roll_no=roll_no).first()
        if existing_student:
            return "Email already registered", 400
        if existing_rollno:
            return "Roll number already registered", 400

        new_student = Student(name=name, semester=semester, roll_no=roll_no, email=email, profile_pic=profile_pic)
        new_student.set_password(password) # Hash the password
        
        #handle image upload
        # if pic:
        #     new_student.profile_pic = pic.read()

        db.session.add(new_student)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('StudentRegister.html')



@app.route('/teacherRegister', methods=['GET', 'POST'])
def teacher_Reg():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('emailAdd')
        password = request.form.get('password')
        #pic = request.files.get('pic') # Removed file handling here

        # Validate form data
        if not name or not email or not password:
            return "All fields are required", 400
        
         # Check if email already exists
        existing_teacher = Teacher.query.filter_by(email=email).first()
        if existing_teacher:
            return "Email already registered", 400

        # Create new teacher
        new_teacher = Teacher(name=name, email=email)
        new_teacher.set_password(password) # Hash the password
        # if pic:
        #     new_teacher.profile_pic = pic.read()

        db.session.add(new_teacher)
        db.session.commit()
        return redirect(url_for('login')) #  Redirect to login or a success page
    return render_template('TeacherRegister.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type') #  Added user type (student or teacher)

        if user_type == 'student':
            user = Student.query.filter_by(email=email).first()
        elif user_type == 'teacher':
            user = Teacher.query.filter_by(email=email).first()
        else:
            return "Invalid user type", 400
        
        if user and user.check_password(password):
            #  Implement your login logic here (e.g., set session)
            session['user_id'] = user.id # store the user's id in a session.
            session['user_type'] = user_type
            
            if user_type == 'student':
                student_data = {
                    'name': user.name,
                    'email': user.email,
                    'semester': user.semester,
                    'roll_no': user.roll_no,
                    'profile_pic': user.profile_pic,
                    'user_type': 'student'
                }
                # session['user_data'] = student_data
                return render_template('dashboardStudent.html', userData=student_data)
            elif user_type == 'teacher':
                teacher_data = {
                    'name': user.name,
                    'email': user.email,
                    'user_type': 'teacher'
                }
                #session['user_data'] = teacher_data  # Removed storing teacher data in session
                return render_template('dashboardTeacher.html', userData=teacher_data) # Redirect teacher to index page
            
        else:
            return "Invalid credentials", 401

    return render_template('login.html')  #  Create a login.html template

# @app.route('/dashboard')
# def dashboard():
#     if 'user_data' in session and session['user_type'] == 'student': #check the user type
#         user_data = session['user_data']
#         return render_template('dashboard.html', userdata=user_data)
#     else:
#         return redirect(url_for('login'))

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('aboutus.html')


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=2004)