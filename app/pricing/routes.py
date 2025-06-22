# app/pricing/routes.py
import pandas as pd
from io import BytesIO
from flask import render_template, flash, redirect, url_for, abort, request, current_app, jsonify
from app import db
from app.pricing import bp
from flask_login import login_required, current_user
from app.models import Ingredient, IngredientPrice # 確保 Ingredient 被匯入
from app.pricing.forms import IngredientPriceForm, UploadPriceForm
from datetime import datetime, timezone

@bp.route('/')
@login_required
def index():
    prices = IngredientPrice.query.filter_by(user=current_user).order_by(IngredientPrice.purchase_date.desc()).all()
    return render_template('pricing/index.html', title='食材價格調查', prices=prices)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_price():
    form = IngredientPriceForm()

    if form.validate_on_submit():
        ingredient_name = form.ingredient_name.data.strip()
        
        # 檢查食材是否已存在於當前使用者的自訂食材庫中
        ingredient = Ingredient.query.filter_by(food_name=ingredient_name, creator=current_user).first()

        if not ingredient:
            # 如果食材不存在，則創建一個新的自訂食材
            ingredient = Ingredient(
                food_name=ingredient_name,
                source='USER', # 標記為用戶自訂食材
                creator=current_user,
                # 其他營養成分欄位預設為 0
                calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                cost_per_unit=0 # 預設成本為0，因為實際成本由 IngredientPrice 管理
            )
            db.session.add(ingredient)
            db.session.flush() # 刷新 session 以便獲取新 ingredient 的 ID
            flash(f'新的食材 "{ingredient_name}" 已自動創建！', 'info')

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
        flash('食材價格紀錄已成功新增！')
        return redirect(url_for('pricing.index'))
    
    return render_template('pricing/add_price.html', title='新增食材價格', form=form)

@bp.route('/edit/<int:price_id>', methods=['GET', 'POST'])
@login_required
def edit_price(price_id):
    price_entry = IngredientPrice.query.get_or_404(price_id)
    if price_entry.user != current_user:
        abort(403) # 非本人無權編輯

    # 使用 obj 填充表單，但對於 ingredient_name 欄位，我們需要手動設定
    form = IngredientPriceForm(obj=price_entry)
    if request.method == 'GET':
        form.ingredient_name.data = price_entry.ingredient.food_name # 將現有的食材名稱填充到表單

    if form.validate_on_submit():
        new_ingredient_name = form.ingredient_name.data.strip()

        # 檢查新的食材名稱是否已存在，或是否與原食材名稱不同
        if new_ingredient_name != price_entry.ingredient.food_name:
            # 如果食材名稱有變，檢查是否要關聯到現有食材，或創建新食材
            target_ingredient = Ingredient.query.filter_by(food_name=new_ingredient_name, creator=current_user).first()
            if not target_ingredient:
                # 如果新的食材名稱不存在，則創建新食材並將價格記錄關聯到新食材
                target_ingredient = Ingredient(
                    food_name=new_ingredient_name,
                    source='USER',
                    creator=current_user,
                    calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                    trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                    cost_per_unit=0
                )
                db.session.add(target_ingredient)
                db.session.flush()
                flash(f'新的食材 "{new_ingredient_name}" 已自動創建並關聯到此價格！', 'info')
            
            # 更新價格記錄的 ingredient 關係
            price_entry.ingredient = target_ingredient
        
        # 更新價格記錄的其他欄位
        price_entry.source = form.source.data
        price_entry.price = form.price.data
        price_entry.quantity = form.quantity.data
        price_entry.unit = form.unit.data

        db.session.commit()
        flash('食材價格紀錄已成功更新！')
        return redirect(url_for('pricing.index'))
    
    return render_template('pricing/edit_price.html', title='編輯食材價格', form=form)


@bp.route('/delete/<int:price_id>', methods=['POST'])
@login_required
def delete_price(price_id):
    price_entry = IngredientPrice.query.get_or_404(price_id)
    if price_entry.user != current_user:
        abort(403)
    
    db.session.delete(price_entry)
    db.session.commit()
    flash('食材價格紀錄已成功刪除。')
    return redirect(url_for('pricing.index'))

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
                
                # 檢查食材是否已存在，如果不存在則創建
                ingredient = Ingredient.query.filter_by(food_name=food_name, creator=current_user).first()
                if not ingredient:
                    ingredient = Ingredient(
                        food_name=food_name,
                        source='USER',
                        creator=current_user,
                        calories_kcal=0, protein_g=0, fat_g=0, saturated_fat_g=0,
                        trans_fat_g=0, carbohydrate_g=0, sugar_g=0, sodium_mg=0,
                        cost_per_unit=0
                    )
                    db.session.add(ingredient)
                    db.session.flush() # 刷新 session 以便獲取 ID

                try:
                    price = float(row['購買價格'])
                    quantity = float(row['購買總數量'])
                    unit = str(row['數量單位']).strip()
                    source = str(row['來源']).strip() if pd.notna(row['來源']) else 'Manual'

                    new_price_entry = IngredientPrice(
                        ingredient=ingredient,
                        user=current_user,
                        source=source,
                        price=price,
                        quantity=quantity,
                        unit=unit
                    )
                    db.session.add(new_price_entry)
                    db.session.commit() # 每次循環提交，以便錯誤時部分數據仍能保存
                    imported_count += 1
                except ValueError:
                    error_rows.append(f"第 {index+2} 行：價格或數量數據格式無效。")
                except Exception as e:
                    error_rows.append(f"第 {index+2} 行：處理資料時發生錯誤 - {e}")
                    db.session.rollback() # 回滾當前行的操作

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

# 輔助路由：獲取食材資訊，可能用於前端計算或顯示 (不變)
@bp.route('/api/ingredient_pricing_info/<int:ingredient_id>')
@login_required
def get_ingredient_pricing_info(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.creator != current_user:
        return jsonify({'status': 'error', 'message': '權限不足'}), 403

    prices_data = []
    for price_entry in ingredient.prices:
        prices_data.append({
            'id': price_entry.id,
            'source': price_entry.source,
            'price': price_entry.price,
            'quantity': price_entry.quantity,
            'unit': price_entry.unit,
            'cost_per_gram': price_entry.calculate_cost_per_gram(),
            'purchase_date': price_entry.purchase_date.strftime('%Y-%m-%d %H:%M')
        })
    
    # 找到最高每克成本
    highest_cost_per_gram = 0
    if prices_data:
        highest_cost_per_gram = max(p['cost_per_gram'] for p in prices_data)
    
    # 返回該食材的所有價格記錄和最高每克成本
    return jsonify({
        'status': 'success',
        'food_name': ingredient.food_name,
        'prices': prices_data,
        'highest_cost_per_gram': highest_cost_per_gram
    })