# --- 完整程式碼，請直接覆蓋 ---

from flask import render_template, flash, redirect, url_for, request
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm # <-- 修改這裡，匯入 LoginForm
from app.models import User
from flask_login import current_user, login_user, logout_user # <-- 修改這裡，匯入登入管理工具

# --- 更新 login 路由 ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # 檢查使用者是否已經登入，如果是，就直接導向首頁
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # 檢查使用者是否存在以及密碼是否正確
        if user is None or not user.check_password(form.password.data):
            flash('無效的使用者名稱或密碼')
            return redirect(url_for('auth.login'))
        
        # 使用 Flask-Login 提供的 login_user 函式來登入使用者
        login_user(user, remember=form.remember_me.data)
        flash(f'歡迎回來, {user.username}!')
        
        # 登入後導向到使用者原本想去的頁面，如果沒有就導向首頁
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='登入', form=form)

# --- 新增 logout 路由 ---
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# --- 原有的 register 路由 (不動) ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('恭喜您，您已成功註冊！現在可以登入了。')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='註冊', form=form)