import os

# 取得專案的根目錄路徑
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    基礎設定類別
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string' # 務必換成一個你自己的密鑰
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'app.db') # 資料庫檔案將存放在根目錄的app.db
    SQLALCHEMY_TRACK_MODIFICATIONS = False