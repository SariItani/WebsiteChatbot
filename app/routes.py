# app/routes.py
import hashlib
import time
from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import requests
from app import app, login_manager, User, db, Message
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


bcrypt = Bcrypt(app)


load_dotenv()

API_KEY = os.getenv('API_KEY')


def calculate_percentage(answers):
    questions = ["""1- Study the given pedigree chart and choose the correct answer
    a- The trait understudy is dominant
    b- Both parents are homozoygous
    c- The trait can be X-linked recessive haemophilia 
    d- The trait understudy is autosomal recessive like cystic fibrosis""",
    """2- The trait studied in the pedigree below is:
    a- Autosomal recessive 
    b- Autosomal dominant 
    c- X-linked recessive
    d- X linked dominant """,
    """3- The trait studied in this pedigree is X-linked recessive. Find the risk of couple 6 and 7 to have an affected child
    a- The risk of female affected is null
    b- The risk of a boy affected is ½
    c- The probability of the mother to carry Xd is 1/2
    d- Only `a` and `b`
    e- All of the above""",
    """4- The pedigree below represents the inheritance of a recessive autosomal disease. Find the risk of child 15 to be affected
    a- The probability of the mother to be heterozygote is ½
    b- The risk is null since both parents are normal
    c- The risk of affected child  is  2/3 x 2/3 x ½ x ½ 
    d-  The risk of affected child is ¼ """,
    """5- Phenylketonuria is a recessive autosomal disease that affects 1/10,000 of newborns world wide. This disease is related to a deficiency in an enzyme called PAH. A study performed on 1,200 children selected from an isolated community, showed that 30 children were heterozygous for PAH. Calculate the proportion of heterozygous children in this community
    a- 30/10,000
    b- 1200/10,000
    c- 30/1200
    d- 1/30""",
    """6- The document below shows the nucleotide sequence of a fragment of the non- transcribed strand of the normal allele (A1) and the allele of the disease (A2) of the PHEX gene. The mutation observed in allele A2 is 
    a- Point mutation by substitution
    b- Point mutation by insertion
    c- Frame-shift mutation by insertion
    d- Frame-shift mutation by addition""",
    """7- The document below shows the transmission of Familial hypophosphatemia in a family. The disease is X-Linked dominant. Indicate the genotypes of individuals 13 and 14
    a- 13: XnY    14: XDXD
    b- 13 XnY     14 XDXn
    c- 13: XnY    14: XDXD or XDXn
    d- 13 nn     14: Dn""",
    """8- The document below shows the transmission of Familial hypophosphatemia in a family. The disease is X-Linked dominant. The risk of individuals 13 and 14 to have affected child is
    a- Null for females, null boys
    b- Half of the females, null boys
    c- Null of the boys, all females are affected
    d- Half of the boys, all females are affected
    e- Half of the females, half of boys are affected""",
    """9- The document below shows the transmission of Familial hypophosphatemia in a family. The disease is X-Linked dominant. Formulate a hypothesis explaining why female 6 is not affected
    a- Female 6 doesn't belong to the family
    b- Female 6 has the diseased masked
    c- Female 6 has turner syndrome, she possesses only 1 X chromosome carrying normal allele
    d- Female 6 is a girl, and girls are not affected."""]
    correct_answers = ['The trait understudy is dominant',
                       'Autosomal recessive',
                       'The risk of female affected is null',
                       'The probability of the mother to be heterozygote is ½',
                       '30/10,000',
                       'Point mutation by substitution',
                       '13: XnY    14: XDXD',
                       'Null for females, null boys',
                       'Female 6 has the diseased masked']
    mistakes = {}
    correct_count = sum(1 for user_answer, correct_answer in zip(answers, correct_answers) if user_answer == correct_answer)
    total_questions = len(correct_answers)
    percentage_correct = (correct_count / total_questions) * 100
    for ans, cor, qst in zip(answers, correct_answers, questions):
        if ans != cor:
            mistakes[qst] = [ans, f"Wrong, should be {cor}."]
        else:
            mistakes[qst] = [cor, "Correct"]
    return percentage_correct, mistakes


def run_conversation(prompt):
    client = OpenAI(api_key=API_KEY)

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    response_text = response.choices[0].message.content

    return response_text


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
@login_required
def index():
    username = current_user.username
    imgpath = current_user.imgpath
    bio = current_user.bio
    return render_template('index.html', username=username, imgpath=imgpath, bio=bio)


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/chat')
@login_required
def chat():
    user = current_user
    chat_history = Message.query.filter_by(sender=user).all()
    for message in chat_history:
        if message.message_type == 'user':
            print("User:", message.content)
        else:
            print("chatgpt:", message.content)
        message.content = message.content.replace('\\n', '<br>')
    if not chat_history:
        message = Message(content="Hello, I will be your biology assistant. Ask me anything to begin!", sender=user, message_type='server')
        db.session.add(message)
        db.session.commit()
        chat_history = [message]
    return render_template('chat.html', chat_history=chat_history)


@app.route('/submit-message', methods=['POST'])
@login_required
def submit_message():
    message_content = request.form['message']

    user = current_user
    message = Message(content=message_content, sender=user, message_type='user')
    db.session.add(message)
    db.session.commit()

    response = run_conversation(prompt=message_content)

    message = Message(content=response, sender=user, message_type='server')
    db.session.add(message)
    db.session.commit()

    return redirect(url_for('chat'))


@app.route('/mcq')
@login_required
def mcq():
    return render_template('mcq.html')


@app.route('/qst', methods=['POST', 'GET'])
@login_required
def qst():
    if request.method == 'POST':
        answers = [value for value in request.form.values()]
        percentage, summary = calculate_percentage(answers)
        display_message = f"Percentage of correct answers: {percentage}%\n"
        for i, (question, response) in enumerate(summary.items(), 1):
            display_message += f"Question {i}:\n"
            if response[1] == "Correct":
                display_message += "Answered Correctly!\n"
            else:
                correct_answer = response[1].replace("Wrong, should be ", "")
                display_message += f"Your Answer: {response[0]}\nCorrect Answer: {correct_answer}\n"
        summary_message = f"You are a teacher's assistant assessing a student's biology MCQ results. If there was a wrong answer, try to break down and explain the question and relate it to the given correct answer. Take a look at the results:\nPercentage of correct answers: {percentage}%\nSummary of answers:\n"
        for question, response in summary.items():
            summary_message += f"{question}: {response[0]} - {response[1]}\n"
        message_content = summary_message
        user = current_user
        message = Message(content=display_message, sender=user, message_type='user')
        db.session.add(message)
        db.session.commit()
        response = run_conversation(prompt=message_content)
        message = Message(content=response, sender=user, message_type='server')
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('chat'))
    return render_template('qst.html')


UPLOAD_FOLDER = 'app/static/assets/img/profilepics'
ALLOWED_EXTENSIONS = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'svg', 'webp']

def allowed_file(filename):
    file_ext = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and file_ext in ALLOWED_EXTENSIONS

def generate_filename(username, extension):
    unique_string = f"{username}{time.time()}"
    hashed_string = hashlib.sha256(unique_string.encode()).hexdigest()
    return f"{hashed_string}.{extension}"

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    imgpath = current_user.imgpath
    if request.method == 'POST':
        username = request.form.get('username').strip()
        bio = request.form.get('bio').strip()
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = generate_filename(username, extension)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                imgpath = f'assets/img/profilepics/{filename}'
                if current_user.imgpath and current_user.imgpath != imgpath:
                    old_img_path = os.path.join(UPLOAD_FOLDER, current_user.imgpath.split('/')[-1])
                    if os.path.exists(old_img_path):
                        os.remove(old_img_path)
        if username!="" and username != current_user.username:
            current_user.username = username
        if bio and bio != current_user.bio:
            current_user.bio = bio
        if imgpath and imgpath != current_user.imgpath:
            current_user.imgpath = imgpath
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', imgpath=imgpath)


@app.route('/future')
@login_required
def future():
    return render_template('future.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/sign-up', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        existing_user_username = User.query.filter_by(username=username).first()
        existing_user_email = User.query.filter_by(email=email).first()

        if existing_user_username:
            flash('Username is already taken. Please choose a different one.', 'danger')
        elif existing_user_email:
            flash('Email is already taken. Please choose a different one.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed_password, imgpath="assets/img/avataaars.svg", bio="Enter bio in the Profile Section...")
            db.session.add(user)
            db.session.commit()

            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('sign-up.html')
