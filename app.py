from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from playwright.sync_api import sync_playwright
import bcrypt, uuid, time, os

ADMIN_PASSWORD = os.environ['ADMIN_PASSWORD']
CLOCK_SEQUENCE = int(os.environ['CLOCK_SEQUENCE'])
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
db = SQLAlchemy(app)

class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    reset_code = db.Column(db.String(50), nullable=True, unique=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Contact(db.Model):
    cid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(500), nullable=False)

    def __init__(self, name, email, desc):
        self.name = name
        self.email = email
        self.desc = desc

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            if len(username)<1 or len(password)<1:
                return render_template('login.html', msg='No field should contain an empty value!')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['username'] = user.username
                session['reset_code'] = user.reset_code
                return redirect('/dashboard')
            else:
                return render_template('login.html', msg='Invalid credentials!')
        except:
            return render_template('login.html', msg='An Error occured while processing your request!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            if len(username)<1 or len(email)<1 or len(password)<1:
                return render_template('register.html', msg='No field should contain an empty value!')
            if User.query.filter_by(username=username).first():
                return render_template('register.html', msg='This username already exists!')
            user = User(username, email, password)
            db.session.add(user)
            db.session.commit()
            return render_template('register.html', msg='Account created!')
        except:
            return render_template('register.html', msg='An Error occured while processing your request!')
    return render_template('register.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            desc = request.form['msg']
            if len(name)<1 or len(email)<1 or len(desc)<1:
                return render_template('contact.html', msg='No field should contain an empty value!')
            contact_query = Contact(name, email, desc)
            db.session.add(contact_query)
            db.session.commit()
            bot_visit()
            return render_template('contact.html', msg='Your message was sent to the administrators. They will review and get back to you shortly!')
        except:
            return render_template('contact.html', msg='An Error occured while processing your request!')
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard():
    try:
        if session['username']=='admin':
            user = User.query.filter_by(username=session['username']).first()
            contact_data = Contact.query.all()
            return render_template('admindashboard.html', user=user, contact_data=contact_data)
        else:
            user = User.query.filter_by(username=session['username']).first()
            return render_template('userdashboard.html', user=user)
    except:
        return redirect('/')

@app.route('/reset/password/<reset_code>', methods=['GET', 'POST'])
def reset_password(reset_code):
    if request.method == 'POST':
        try:
            password = request.form['password']
            user = User.query.filter_by(reset_code=reset_code).first()
            if not user:
                return 'Reset code is incorrect'
            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db.session.commit()
            return 'Password changed!'
        except:
            return redirect('/')
    return render_template('reset.html', reset_code=reset_code)

@app.route('/resetcode')
def resetcode():
    try:
        if session['username']:
            reset_code = str(uuid.uuid1(clock_seq=CLOCK_SEQUENCE))
            user = User.query.filter_by(username=session['username']).first()
            user.reset_code = reset_code
            db.session.commit()
            session['reset_code'] = user.reset_code
            # TODO: Add code to send reset code to users through email or other means.
            return redirect('/dashboard')
        return redirect('/')
    except:
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/protected', methods=['POST'])
def protected():
    try:
        if session['username']=='admin':
            if request.method == 'POST':
                try:
                    password = request.form['password']
                    user = User.query.filter_by(username='admin').first()
                    if user and user.check_password(password):
                        flag = ''
                        with open('./flag.txt') as f:
                            flag += f.readline()
                        return flag
                    return 'Wrong password!'
                except:
                    return 'An Error occurred'
        return redirect('/dashboard')
    except:
        return redirect('/')

def bot_visit():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    page.goto('http://127.0.0.1:1337/')
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('.btn')
    time.sleep(0.1)
    context.close()
    browser.close()
    playwright.stop()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337)
