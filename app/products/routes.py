# app/products/routes.py
from flask import render_template, flash, redirect, url_for, abort, request, current_app, jsonify
from app import db
from app.products import bp
from flask_login import login_required, current_user
from app.models import Product, Recipe
from app.products.forms import ProductForm

# 固定費率，您可以根據實際情況調整這些值
ELECTRICITY_COST_PER_KWH = 3.0 # 每度電費 (NTD/kWh)
LABOR_COST_PER_HOUR = 200.0   # 每小時人力成本 (NTD/小時)

@bp.route('/')
@login_required
def index():
    # 獲取所有產品，用於左側面板
    all_products = Product.query.filter_by(creator=current_user).order_by(Product.product_name).all()
    products_data_for_display = [{'id': p.id, 'name': p.product_name} for p in all_products]

    # 獲取所有食譜，用於新增產品時的 Modal
    all_recipes = Recipe.query.filter_by(author=current_user).order_by(Recipe.recipe_name).all()
    recipes_data_for_display = []
    for recipe in all_recipes:
        recipe_calc_data = recipe.calculate_nutrition()
        recipes_data_for_display.append({
            'id': recipe.id,
            'name': recipe.recipe_name,
            'total_ingredient_cost': round(recipe_calc_data.get('total_ingredient_cost', 0), 2),
            'servings_count': recipe.servings_count
        })

    return render_template(
        'products/index.html',
        title='產品管理',
        all_products_initial_data=products_data_for_display,
        all_recipes_initial_data=recipes_data_for_display,
        electricity_cost_per_kwh=ELECTRICITY_COST_PER_KWH,
        labor_cost_per_hour=LABOR_COST_PER_HOUR
    )

# --- API 路由 ---

# [保留] 建立新產品的 API
@bp.route('/api/create_product', methods=['POST'])
@login_required
def api_create_product():
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    recipe = Recipe.query.get(data.get('recipe_id'))
    if not recipe or recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '食譜不存在或無權限'}), 404
    
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
            production_time_hr=float(data.get('production_time_hr', 0)),
            calculated_cost=float(data.get('calculated_cost', 0))
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'產品 "{product.product_name}" 已成功建立！'})
    except (ValueError, TypeError) as e:
        return jsonify({'status': 'error', 'message': f'數據格式錯誤: {e}'}), 400

# [新增] 獲取單一產品詳細資料的 API
@bp.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
    
    # 獲取產品關聯的食譜的詳細資料，用於成本計算
    recipe_details = product.recipe.calculate_nutrition()
    
    return jsonify({
        'status': 'success',
        'id': product.id,
        'product_name': product.product_name,
        'description': product.description,
        'selling_price': product.selling_price,
        'stock_quantity': product.stock_quantity,
        'batch_size': product.batch_size,
        'bake_power_w': product.bake_power_w,
        'bake_time_min': product.bake_time_min,
        'production_time_hr': product.production_time_hr,
        'recipe_id': product.recipe_id,
        'recipe_details': {
            'total_ingredient_cost': recipe_details.get('total_ingredient_cost', 0),
            'servings_count': product.recipe.servings_count
        }
    })

# [新增] 更新產品的 API
@bp.route('/api/products/<int:product_id>/update', methods=['POST'])
@login_required
def update_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
        
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    try:
        product.product_name = data.get('product_name', product.product_name)
        product.description = data.get('description', product.description)
        product.selling_price = float(data.get('selling_price', product.selling_price))
        product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
        product.batch_size = int(data.get('batch_size', product.batch_size))
        product.bake_power_w = float(data.get('bake_power_w', product.bake_power_w))
        product.bake_time_min = float(data.get('bake_time_min', product.bake_time_min))
        product.production_time_hr = float(data.get('production_time_hr', product.production_time_hr))
        product.calculated_cost = float(data.get('calculated_cost', product.calculated_cost))
        db.session.commit()
        return jsonify({'status': 'success', 'message': '產品已成功更新！'})
    except (ValueError, TypeError) as e:
        return jsonify({'status': 'error', 'message': f'數據格式錯誤: {e}'}), 400


# [新增] 刪除產品的 API
@bp.route('/api/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product_api(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '產品已成功刪除。'})


# [保留] 搜尋食譜的 API (用於新增產品的 Modal)
@bp.route('/api/search_recipes', methods=['GET'])
@login_required
def search_recipes():
    query = request.args.get('q', '', type=str)
    base_query = Recipe.query.filter_by(author=current_user)
    if query:
        search = f"%{query}%"
        base_query = base_query.filter(Recipe.recipe_name.like(search))
    recipes = base_query.order_by(Recipe.recipe_name).limit(20).all()
    results = []
    for recipe in recipes:
        recipe_data = recipe.calculate_nutrition()
        results.append({
            'id': recipe.id,
            'name': recipe.recipe_name,
            'total_ingredient_cost': recipe_data.get('total_ingredient_cost', 0),
            'servings_count': recipe.servings_count
        })
    return jsonify(results)


# [保留] 獲取單一食譜詳情的 API (用於新增產品的 Modal)
@bp.route('/api/get_recipe_details/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe_details(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '無權限查看此食譜'}), 403
    
    recipe_data = recipe.calculate_nutrition()
    return jsonify({
        'status': 'success',
        'recipe_id': recipe.id,
        'recipe_name': recipe.recipe_name,
        'servings_count': recipe.servings_count,
        'total_ingredient_cost': recipe_data.get('total_ingredient_cost', 0)
    })

