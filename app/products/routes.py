# app/products/routes.py
import pandas as pd
from io import BytesIO
from flask import render_template, flash, redirect, url_for, abort, request, current_app, jsonify
from app import db
from app.products import bp
from flask_login import login_required, current_user
from app.models import Product, Recipe, Ingredient, IngredientPrice
from app.products.forms import ProductForm
from datetime import datetime, timezone
from sqlalchemy import desc # 確保 desc 被匯入

# 固定費率，您可以根據實際情況調整這些值
ELECTRICITY_COST_PER_KWH = 3.0 # 每度電費 (NTD/kWh)
LABOR_COST_PER_HOUR = 200.0   # 每小時人力成本 (NTD/小時)

@bp.route('/')
@login_required
def index():
    products = Product.query.filter_by(creator=current_user).order_by(Product.updated_at.desc()).all()
    
    # 獲取所有當前使用者創建的食譜，用於左側面板的初始列表顯示
    all_recipes = Recipe.query.filter_by(author=current_user).order_by(Recipe.recipe_name).all()
    recipes_data_for_display = []
    for recipe in all_recipes:
        recipe_calc_data = recipe.calculate_nutrition()
        recipes_data_for_display.append({
            'id': recipe.id,
            'name': recipe.recipe_name,
            'total_ingredient_cost': round(recipe_calc_data['total_ingredient_cost'], 2),
            'servings_count': recipe.servings_count
        })

    form = ProductForm() # 傳遞一個空的表單實例，用於前端渲染欄位
    
    return render_template(
        'products/index.html',
        title='產品管理',
        products=products,
        form=form,
        all_recipes_initial_data=recipes_data_for_display, # 將所有食譜數據傳遞給模板
        electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
        labor_cost_per_hour=LABOR_COST_PER_HOUR
    )

# 移除 create_from_recipe 路由，因為功能將整合到 index 頁面
# @bp.route('/create/<int:recipe_id>', methods=['GET', 'POST'])
# @login_required
# def create_from_recipe(recipe_id):
#     # ... (此路由的內容已被移除或整合到前端)

@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        abort(403)

    # 重新計算食譜的食材成本細項，確保是最新的
    recipe_calculated_data = product.recipe.calculate_nutrition()
    
    form = ProductForm(obj=product) # 用現有產品數據填充表單

    if form.validate_on_submit():
        form.populate_obj(product)
        product.updated_at = datetime.now(timezone.utc)
        
        # 重新計算並更新產品的總成本
        total_costs = product.calculate_total_product_cost(
            electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
            labor_cost_per_hour=LABOR_COST_PER_HOUR
        )
        product.calculated_cost = total_costs['average_cost_per_product'] # 更新每個產品的平均總成本

        db.session.commit()
        flash(f'產品 "{product.product_name}" 已成功更新！')
        return redirect(url_for('products.index'))
    
    # 將所有成本細項和食譜數據傳遞給模板
    total_costs_display = product.calculate_total_product_cost(
        electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
        labor_cost_per_hour=LABOR_COST_PER_HOUR
    )

    return render_template(
        'products/edit_product.html',
        title=f'編輯產品: {product.product_name}',
        form=form,
        product=product,
        recipe_calculated_data=recipe_calculated_data, # 食譜的營養和食材成本詳情
        total_costs_display=total_costs_display, # 產品總成本的詳細計算結果
        electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
        labor_cost_per_hour=LABOR_COST_PER_HOUR
    )

@bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        abort(403)
    
    product_name = product.product_name
    db.session.delete(product)
    db.session.commit()
    flash(f'產品 "{product_name}" 已成功刪除。')
    return redirect(url_for('products.index'))

# 新增 API 路由來處理產品的建立 (從前端 JS 發送)
@bp.route('/api/create_product', methods=['POST'])
@login_required
def api_create_product():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    recipe_id = data.get('recipe_id')
    recipe = Recipe.query.get(recipe_id)
    if not recipe or recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '食譜不存在或無權限'}), 404

    # 直接從 JSON 數據中獲取，不使用 WTForms，因為表單驗證在前端已處理或需要更彈性的 API 處理
    # 這裡可以加入更詳細的數據驗證邏輯，或創建一個 ProductForm 並使用 form.process(data=data) + form.validate()
    # 為了簡潔性，這裡直接取用數據
    try:
        product = Product(
            product_name=data.get('product_name'),
            description=data.get('description'),
            selling_price=float(data.get('selling_price', 0)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            creator=current_user,
            recipe=recipe,
            batch_size=int(data.get('batch_size', 1)),
            bake_power_w=float(data.get('bake_power_w', 0)),
            bake_time_min=float(data.get('bake_time_min', 0)),
            production_time_hr=float(data.get('production_time_hr', 0))
        )
        
        # 計算並保存最終的產品總成本
        total_costs = product.calculate_total_product_cost(
            electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
            labor_cost_per_hour=LABOR_COST_PER_HOUR
        )
        product.calculated_cost = total_costs['average_cost_per_product']

        db.session.add(product)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'產品 "{product.product_name}" 已成功建立！', 'product_id': product.id})
    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'數據格式錯誤: {e}'}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating product via API: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': '建立產品時發生錯誤'}), 500


# 新增 API 路由來搜尋食譜
@bp.route('/api/search_recipes', methods=['GET'])
@login_required
def search_recipes():
    query = request.args.get('q', '', type=str)
    
    # 搜尋當前使用者創建的食譜
    base_query = Recipe.query.filter_by(author=current_user)
    if query:
        search = f"%{query}%"
        base_query = base_query.filter(Recipe.recipe_name.like(search))
    
    recipes = base_query.order_by(Recipe.recipe_name).limit(10).all() # 限制結果數量
    
    results = []
    for recipe in recipes:
        # 計算食譜的食材總成本，以便在搜尋結果中顯示
        recipe_data = recipe.calculate_nutrition()
        results.append({
            'id': recipe.id,
            'name': recipe.recipe_name,
            'total_ingredient_cost': round(recipe_data['total_ingredient_cost'], 2),
            'servings_count': recipe.servings_count
        })
    return jsonify(results)

# 新增 API 路由來獲取單個食譜的詳細信息，包含成本細項
@bp.route('/api/get_recipe_details/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe_details(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '無權限查看此食譜'}), 403
    
    recipe_data = recipe.calculate_nutrition()

    return jsonify({
        'status': 'success',
        'recipe_name': recipe.recipe_name,
        'servings_count': recipe.servings_count,
        'total_weight_g': round(recipe_data['total_weight_g'], 1),
        'total_ingredient_cost': round(recipe_data['total_ingredient_cost'], 2),
        'ingredient_cost_details': [
            {
                'ingredient_name': item['ingredient_name'],
                'quantity_g': round(item['quantity_g'], 1),
                'cost_per_gram': round(item['cost_per_gram'], 4),
                'item_total_cost': round(item['item_total_cost'], 2),
                'cost_source': item.get('cost_source', ''),
                'purchase_unit': item.get('purchase_unit', '')
            } for item in recipe_data['ingredient_cost_details']
        ]
    })