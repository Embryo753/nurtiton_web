# --- 再次確認此檔案的完整內容 ---
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app) # <--- 確認這行存在

    # 註冊藍圖
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.recipes import bp as recipes_bp
    app.register_blueprint(recipes_bp, url_prefix='/recipes')

    return app

# --- 確認這行在檔案的最底部 ---
from app import models