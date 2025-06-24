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
            
            ingredient = Ingredient.query.filter_by(food_name=ingredient_name, creator=current_user).first()
            
            if not ingredient:
                ingredient = Ingredient.query.filter_by(food_name=ingredient_name, source='TFDA').first()

            if not ingredient:
                ingredient = Ingredient(
                    food_name=ingredient_name,
                    source='USER',
                    creator=current_user,
                    calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                    trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                    cost_per_unit=0
                )
                db.session.add(ingredient)
                db.session.flush()
                flash_message = f'新的自訂食材 "{ingredient_name}" 已自動創建！'
            else:
                flash_message = f'已為現有食材 "{ingredient_name}" 新增價格！'

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

        # 在 POST 請求中，我們只處理表單數據，所以不需要傳遞 obj
        form = IngredientPriceForm(data=data)
        if form.validate():
            # 由於食材名稱是 readonly，我們不更新它，只更新其他欄位
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

    # --- 修改處：確保 GET 請求時，表單能正確填充資料 ---
    # 在 GET 請求時，使用 obj 參數來從資料庫物件填充表單
    form = IngredientPriceForm(obj=price_entry)
    # 手動設定不可編輯的食材名稱欄位
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

# 以下是 upload_prices 和 API 路由，保持不變
@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_prices():
    form = UploadPriceForm()
    if form.validate_on_submit():
        f = form.csv_file.data
        if not f:
            flash('請選擇檔案！', 'danger')
            return redirect(url_for('pricing.upload_prices'))

        filename = f.filename
        if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
            flash('僅支援 CSV 或 Excel 檔案！', 'danger')
            return redirect(url_for('pricing.upload_prices'))
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(f.read()))
            else: # .xlsx
                df = pd.read_excel(BytesIO(f.read()))

            required_columns = ['食材名稱', '來源', '購買價格', '購買總數量', '數量單位']
            if not all(col in df.columns for col in required_columns):
                flash(f'匯入失敗：檔案中缺少必要欄位。需要欄位: {", ".join(required_columns)}', 'danger')
                return redirect(url_for('pricing.upload_prices'))

            imported_count = 0
            error_rows = []
            for index, row in df.iterrows():
                food_name = str(row['食材名稱']).strip()
                
                # 採用與 add_price 相同的查找邏輯
                ingredient = Ingredient.query.filter_by(food_name=food_name, creator=current_user).first()
                if not ingredient:
                    ingredient = Ingredient.query.filter_by(food_name=food_name, source='TFDA').first()
                
                if not ingredient:
                    ingredient = Ingredient(
                        food_name=food_name, source='USER', creator=current_user,
                        calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                        trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                        cost_per_unit=0
                    )
                    db.session.add(ingredient)
                    db.session.flush()

                try:
                    price = float(row['購買價格'])
                    quantity = float(row['購買總數量'])
                    unit = str(row['數量單位']).strip()
                    source = str(row['來源']).strip() if pd.notna(row['來源']) else 'Manual'

                    new_price_entry = IngredientPrice(
                        ingredient=ingredient, user=current_user, source=source,
                        price=price, quantity=quantity, unit=unit
                    )
                    db.session.add(new_price_entry)
                    db.session.commit()
                    imported_count += 1
                except (ValueError, TypeError):
                    db.session.rollback()
                    error_rows.append(f"第 {index+2} 行：價格或數量數據格式無效。")
                except Exception as e:
                    db.session.rollback()
                    error_rows.append(f"第 {index+2} 行：處理資料時發生錯誤 - {e}")

            if imported_count > 0:
                flash(f'成功匯入 {imported_count} 筆價格紀錄！', 'success')
            if error_rows:
                flash(f'匯入完成，但有 {len(error_rows)} 筆紀錄失敗：' + "; ".join(error_rows), 'warning')
            
            return redirect(url_for('pricing.index'))

        except Exception as e:
            current_app.logger.error(f"Error during price import: {e}", exc_info=True)
            flash(f'檔案處理失敗：{e}', 'danger')
            return redirect(url_for('pricing.upload_prices'))

    return render_template('pricing/upload_prices.html', title='匯入食材價格', form=form)

@bp.route('/api/ingredient_pricing_info/<int:ingredient_id>')
@login_required
def get_ingredient_pricing_info(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    # 允許查看 TFDA 食材的價格，所以移除 creator 檢查
    # if ingredient.creator != current_user and ingredient.source != 'TFDA':
    #     return jsonify({'status': 'error', 'message': '權限不足'}), 403

    prices_data = []
    # 只查找當前使用者為該食材建立的價格
    user_prices = ingredient.prices.filter_by(user_id=current_user.id).all()
    
    for price_entry in user_prices:
        prices_data.append({
            'id': price_entry.id,
            'source': price_entry.source,
            'price': price_entry.price,
            'quantity': price_entry.quantity,
            'unit': price_entry.unit,
            'cost_per_gram': price_entry.calculate_cost_per_gram(),
            'purchase_date': price_entry.purchase_date.strftime('%Y-%m-%d %H:%M')
        })
    
    latest_cost_per_gram = 0
    if prices_data:
        latest_price = sorted(prices_data, key=lambda p: p['purchase_date'], reverse=True)[0]
        latest_cost_per_gram = latest_price['cost_per_gram']
    
    return jsonify({
        'status': 'success',
        'food_name': ingredient.food_name,
        'prices': prices_data,
        'latest_cost_per_gram': latest_cost_per_gram
    })
