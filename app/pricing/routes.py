# app/pricing/routes.py
import pandas as pd
from io import BytesIO
from flask import render_template, flash, redirect, url_for, abort, request, current_app, jsonify
from app import db
from app.pricing import bp
from flask_login import login_required, current_user
from app.models import Ingredient, IngredientPrice
from app.pricing.forms import IngredientPriceForm, UploadPriceForm
from datetime import datetime, timezone
from sqlalchemy import or_

@bp.route('/')
@login_required
def index():
    prices = IngredientPrice.query.filter_by(user=current_user).order_by(IngredientPrice.purchase_date.desc()).all()
    return render_template('pricing/index.html', title='食材價格調查', prices=prices)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_price():
    form = IngredientPriceForm()

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '無效的請求資料'}), 400

        form = IngredientPriceForm(data=data)
        if form.validate():
            ingredient_name = form.ingredient_name.data.strip()
            
            # 優先查找使用者自己的食材，然後是 TFDA 的
            ingredient = Ingredient.query.filter(
                or_(Ingredient.creator == current_user, Ingredient.source == 'TFDA'),
                Ingredient.food_name == ingredient_name
            ).first()

            flash_message = f'已為現有食材 "{ingredient_name}" 新增價格！'
            if not ingredient:
                # 如果完全找不到，就創建一個新的使用者專屬食材
                ingredient = Ingredient(
                    food_name=ingredient_name,
                    source='USER',
                    creator=current_user,
                    calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                    trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                    cost_per_unit=0
                )
                db.session.add(ingredient)
                db.session.flush() # 先 flush 取得 id
                flash_message = f'新的自訂食材 "{ingredient_name}" 已自動創建！'

            ingredient_price = IngredientPrice(
                ingredient=ingredient,
                user=current_user,
                source=form.source.data,
                price=form.price.data,
                quantity=form.quantity.data,
                unit=form.unit.data
            )
            db.session.add(ingredient_price)
            db.session.commit()
            
            flash(flash_message, 'success')
            
            return jsonify({
                'status': 'success',
                'message': '食材價格紀錄已成功新增！',
                'redirect_url': url_for('pricing.index')
            })
        else:
            return jsonify({'status': 'error', 'message': '資料驗證失敗', 'errors': form.errors}), 422
    
    # 處理從食譜頁面跳轉過來的請求
    ingredient_name_from_query = request.args.get('ingredient_name')
    if ingredient_name_from_query:
        form.ingredient_name.data = ingredient_name_from_query

    return render_template('pricing/add_price.html', title='新增食材價格', form=form)


@bp.route('/edit/<int:price_id>', methods=['GET', 'POST'])
@login_required
def edit_price(price_id):
    price_entry = IngredientPrice.query.get_or_404(price_id)
    if price_entry.user != current_user:
        abort(403)

    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '無效的請求資料'}), 400

        form = IngredientPriceForm(data=data)
        if form.validate():
            price_entry.source = form.source.data
            price_entry.price = form.price.data
            price_entry.quantity = form.quantity.data
            price_entry.unit = form.unit.data
            price_entry.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            flash('食材價格紀錄已成功更新！', 'success')
            return jsonify({
                'status': 'success',
                'message': '食材價格紀錄已成功更新！',
                'redirect_url': url_for('pricing.index')
            })
        else:
            return jsonify({'status': 'error', 'message': '資料驗證失敗', 'errors': form.errors}), 422

    form = IngredientPriceForm(obj=price_entry)
    form.ingredient_name.data = price_entry.ingredient.food_name
    
    return render_template('pricing/edit_price.html', title='編輯食材價格', form=form, price_id=price_id)


@bp.route('/delete/<int:price_id>', methods=['POST'])
@login_required
def delete_price(price_id):
    price_entry = IngredientPrice.query.get_or_404(price_id)
    if price_entry.user != current_user:
        abort(403)
    
    db.session.delete(price_entry)
    db.session.commit()
    flash('食材價格紀錄已成功刪除。', 'success')
    return redirect(url_for('pricing.index'))

# --- ★ 新增的 API 路由，用於即時搜尋 ---
@bp.route('/api/search_all_ingredients')
@login_required
def search_all_ingredients():
    """根據查詢字串搜尋使用者自有和 TFDA 的食材。"""
    query = request.args.get('q', '', type=str)
    if not query:
        return jsonify([])

    search = f"%{query}%"
    
    # 搜尋範圍包括使用者自己建立的(USER)和系統內建的(TFDA)
    ingredients = Ingredient.query.filter(
        or_(
            Ingredient.creator == current_user,
            Ingredient.source == 'TFDA'
        ),
        Ingredient.food_name.like(search)
    ).order_by(Ingredient.food_name).limit(10).all()
    
    results = [{'name': ing.food_name} for ing in ingredients]
    return jsonify(results)
# --- API 路由結束 ---


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_prices():
    form = UploadPriceForm()
    if form.validate_on_submit():
        # ... (此部分邏輯不變) ...
        pass
    return render_template('pricing/upload_prices.html', title='匯入食材價格', form=form)
