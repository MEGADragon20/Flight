#assemble app from blueprints
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv
import os

from blueprints.account import return_account_blueprint
load_dotenv()
USE_REDIS = os.getenv("USE_REDIS")
REDIS_URL = os.getenv("REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY


    from blueprints.account import return_account_blueprint
    from blueprints.game import return_game_blueprint

    account_bp = return_account_blueprint()
    game_bp = return_game_blueprint()

    # THIS is the important line

    app.register_blueprint(account_bp)
    app.register_blueprint(game_bp, url_prefix='/<username>/game')


    # this create first user + game session

    return app