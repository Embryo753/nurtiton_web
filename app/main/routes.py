# --- 完整程式碼，請直接覆蓋 ---
from flask import render_template
from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    # 修正點：從直接回傳文字，改成渲染一個HTML樣板
    return render_template('main/index.html', title='首頁')