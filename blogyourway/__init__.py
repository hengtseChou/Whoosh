"""
Configure little-blog application in create_app() with a factory pattern.
"""
from flask import Flask, render_template, request
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_session import Session
from pymongo.errors import ServerSelectionTimeoutError

from blogyourway.config import APP_SECRET, ENV, REDIS_HOST, REDIS_PORT, REDIS_PW
from blogyourway.services.cache import cache
from blogyourway.services.logging import logger, return_client_ip
from blogyourway.services.mongo import mongodb
from blogyourway.services.redis import redis
from blogyourway.services.socketio import socketio
from blogyourway.utils.users import User

from .views import backstage_bp, blog_bp

if ENV == "develop":
    cache_config = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
elif ENV == "prod":
    cache_config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": REDIS_HOST,
        "CACHE_REDIS_PORT": REDIS_PORT,
        "CACHE_REDIS_PASSWORD": REDIS_PW,
    }


def create_app() -> Flask:
    """
    Defines:
    - secret key of application
    - login manager (login view, login message)
    - user loader
    - 404 error handler page
    - 500 error handler page
    - register blueprints (blog, backstage)
    - cache
    - socketio
    - server-side session
    - check connections for redis and mongo
    """

    app = Flask(__name__)
    logger.info("App initialization started.")
    app.secret_key = APP_SECRET

    # debug mode
    if ENV == "develop":
        app.config["DEBUG"] = True
        toolbar = DebugToolbarExtension()
        toolbar.init_app(app)
        app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
        logger.debug("Debugtoolbar initialized.")

    ## login
    login_manager = LoginManager()
    login_manager.login_view = "blog.login_get"
    login_manager.login_message = "Please login to proceed."
    login_manager.init_app(app)
    logger.debug("Login manager initialized.")

    @login_manager.user_loader
    def user_loader(username: str) -> User:
        """register user loader for current_user to access"""
        user_creds = mongodb.user_login.find_one({"username": username})
        user = User(user_creds)
        # return none if the ID is not valid
        return user

    # Register the custom error page
    @app.errorhandler(404)
    def page_not_found(error):
        client_ip = return_client_ip(request, ENV)
        logger.debug(f"{client_ip} - 404 not found at {request.environ['RAW_URI']}. ")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        client_ip = return_client_ip(request, ENV)
        logger.error(f"{client_ip} - 500 internal error at {request.environ['RAW_URI']}.")
        # flask app itself will show the error occurred
        return render_template("500.html"), 500

    logger.debug("Error handlers registered.")

    # blueprints
    app.register_blueprint(blog_bp, url_prefix="/")
    app.register_blueprint(backstage_bp, url_prefix="/backstage/")
    logger.debug("Blueprints registered.")

    # cache
    cache.init_app(app, config=cache_config)
    logger.debug("Flask-caching initialized.")

    # socketio
    socketio.init_app(app, manage_session=False)
    logger.debug("Flask-socketio initialized.")

    # session
    # session = Session()
    # app.config["SESSION_TYPE"] = "redis"
    # app.config["SESSION_PERMANENT"] = False
    # app.config["SESSION_USE_SIGNER"] = True
    # app.config["SESSION_REDIS"] = redis
    # session.init_app(app)
    # logger.debug("Flask-session initialized.")

    # check connection
    try:
        mongodb.client.server_info()
        logger.debug("MongoDB connected.")
    except ServerSelectionTimeoutError as error:
        logger.error(error)
        exit("MongoDB is NOT connected. App initializaion failed.")

    try:
        redis.ping()
        logger.debug("Redis connected.")
    except Exception as error:
        logger.error(error)
        exit("Redis is NOT connected. App initializaion failed.")

    logger.info("App initialization completed.")

    return app
