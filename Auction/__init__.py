from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

def create_app():
    # creating and initialising a flask app instance
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "very secret message"
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"
    db.init_app(app) # connecting db with app

    login_manager = LoginManager()
    login_manager.login_view = 'auth_views.signin'  # setting our login view as the signin function in auth_views.py
    login_manager.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):   # loads user in the flask database
        return User.query.get(int(user_id))

    # using 2 blueprints, one for authentication purpose and other for other functionalities
    from Auction.views import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from Auction.auth_views import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app

app = create_app()