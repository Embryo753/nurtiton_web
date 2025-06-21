from flask import Blueprint

# 建立一個名為 'recipes' 的藍圖
bp = Blueprint('recipes', __name__)

# 從目前資料夾(.)匯入路由模組
from . import routes