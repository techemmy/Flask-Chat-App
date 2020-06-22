#! usr/env/bin python
from flask import (Flask, render_template, request, url_for,
                   redirect, flash, session)
import os
from flask_session import Session
from models import db, User
from forms import SignUpForm
from passlib.hash import sha256_crypt
from functools import wraps


# returns flask application objects
def create_app(test_config=None):
    """ application's factory """
    app = Flask(__name__)

    # secret key autogenerated
    SECRET_KEY = os.urandom(32)

    app.config.from_mapping(
        SESSION_PERMANENT=False,
        SESSION_TYPE="filesystem",
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=SECRET_KEY,
    )

    if test_config is None:
        # load the app config from file if not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # if testing load app config on tests config
        app.config.from_mapping(test_config)

    def login_required(f):
        """ user login check wrapper """
        @wraps(f)
        def wrap(*args, **kwargs):
            """ checks if user in session """
            if session.get('user'):
                return f(*args, **kwargs)
            else:
                flash("You need to login first")
                return redirect(url_for('login'))
        return wrap

    def logout_required(f):
        """ user logout check wrapper """
        @wraps(f)
        def wrapped_view(*args, **kwargs):
            """ checks if user not in session """
            if not session.get('user'):
                return f(*args, **kwargs)
            else:
                # if user in session redirects to chat
                flash('You need to logout first.')
                return redirect(url_for('chat'))
        return wrapped_view

    @app.route('/<path:urlpath>/')
    @app.route('/', methods=['POST', 'GET'])
    @logout_required
    def index(urlpath='/'):
        """ homepage for all non-registered users """
        # if user not in session, form pop's up
        form = SignUpForm()
        return render_template('main/home.html', form=form)

    @app.route('/sign-up/', methods=['POST', 'GET'])
    @logout_required
    def sign_up():
        """ registers user on post request """
        form = SignUpForm()
        print("validating...")
        # validate users information and form submissioin
        if form.validate_on_submit():
            try:
                hashed_password = sha256_crypt.hash(form.password.data)
                firstname = form.firstname.data
                lastname = form.lastname.data
                username = form.username.data
                email = form.email.data
                password = hashed_password
                terms = form.tos.data
                existing_user = User.query.filter_by(username=username).first()
                u = User.query.filter_by(email=email).first()
                # checks if username exists before, if true error
                if existing_user is None:
                    if u is None:
                        # adds user to db
                        new_user = User(firstname=firstname, lastname=lastname,
                                        username=username, email=email,
                                        password=password, terms=terms)
                        new_user.save()
                        print("validated...")
                        flash("You have been signed up successfully! \
                               Now login your details")
                        return redirect(url_for('login'))
                    else:
                        # email taken error flash
                        flash("Email taken already")
                else:
                    # username exists error flash
                    flash("Username already exists.")
            except Exception as e:
                print(e)
                return redirect(url_for('index'))
        return render_template('main/home.html', form=form)

    @app.route('/login/', methods=['POST', 'GET'])
    @logout_required
    def login():
        """ verify if user exists in the database """
        try:
            if request.method == "POST":
                # checks if user exists
                username = request.form.get('username')
                password = request.form.get('password')
                u = User.query.filter_by(username=username).first()
                v = sha256_crypt.verify(password, u.password)
                if u and v:
                    # logs user in
                    print("Validated!")
                    session["user"] = u
                    flash("You are now logged in!")
                    return redirect(url_for('chat'))
                else:
                    flash(f"Invalid Login Details!")
        except Exception as e:
            flash('Check your credentials and try again!')
            print('Error------>', e)

        return render_template('main/login.html')

    @app.route("/logout/")
    @login_required
    def logout():
        """ logs out user """
        session.clear()
        flash("You logged out successfully!")
        return redirect(url_for('index'))

    @app.route('/chat/')
    @login_required
    def chat():
        """ chat page if user is logged in """
        return render_template('main/chat.html')

    # initializes app and configures sessions
    db.init_app(app)
    Session(app)

    return app


# initializes db on cli call
def main():
    """ initialize db """
    print("Initializing db")
    db.create_all()


if __name__ == "__main__":
    create_app().app_context().push()
    # initializes db on cli call
    main()
