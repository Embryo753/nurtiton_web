import os

# 取得專案的根目錄路徑
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    應用程式的基礎設定類別。
    """
    
    # 用於保護 session 和 CSRF 的密鑰
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-and-hard-to-guess-string'
    
    # 資料庫的連接 URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
        
    # 關閉 SQLAlchemy 的事件通知系統以節省資源
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ★ 新增設定：讓 jsonify 直接回傳 UTF-8 編碼的 JSON，而不是 ASCII escaped string
    # 這對於處理包含中文的 API 回應非常有幫助。
    JSON_AS_ASCII = False

    # --- 產品成本計算相關的全域設定 ---
    # 每度電費 (NTD/kWh)
    ELECTRICITY_COST_PER_KWH = float(os.environ.get('ELECTRICITY_COST_PER_KWH') or 3.5)

    # 每小時人力成本 (NTD/小時)
    LABOR_COST_PER_HOUR = float(os.environ.get('LABOR_COST_PER_HOUR') or 200.0)

