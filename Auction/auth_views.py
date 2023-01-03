from flask import render_template, Blueprint, url_for, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db

auth = Blueprint('auth_views', __name__)

# for creating user accounts
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.form.get('password') == request.form.get('repassword'):  # checking if 'Password' and 'Confirm Password' matches
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()

            if user:  # blocks a user from using same email to create different accounts
                return render_template("signup.html", error='This email is already taken!')

            name = request.form.get('fname') +' '+ request.form.get('lname')
            password = request.form.get('password')
            user = User(username=name, email=email, password=generate_password_hash(password, method='sha256'))
            db.session.add(user)  # updates user db
            db.session.commit()

            return redirect(url_for('auth_views.signin'))
        else:
            return render_template("signup.html", error='Passwords do not match')

    return render_template("signup.html")

# for logging into account
@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user:  # if user doesn't have an account
            return render_template("signin.html", error='User does not exist')
        if not check_password_hash(user.password, password):  # if password doesn't match
            return render_template("signin.html", error='Wrong password provided')

        login_user(user)

        with open('wallet.log', 'r+') as f:   # initialise wallet of each user to 0 for first-time login
            all_wlts = f.readlines()
            all_wlts_dict = {}
            for wallet in all_wlts:
                w = list(map(int, wallet.split(',')))
                all_wlts_dict[w[0]] = w[1]
            if len(all_wlts) == 0:
                f.write(str(user.id) + ',0')
            elif user.id not in all_wlts_dict:
                f.write('\n' + str(user.id) + ',0')
        
        return redirect(url_for('views.index'))

    return render_template("signin.html")

# logging out
@auth.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('views.index'))