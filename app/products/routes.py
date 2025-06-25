# app/products/routes.py
from flask import render_template, flash, redirect, url_for, abort, request, current_app, jsonify
from app import db
from app.products import bp
from flask_login import login_required, current_user
from app.models import Product, Recipe
from app.products.forms import ProductForm

@bp.route('/')
@login_required
def index():
    # ... 此函數保持不變 ...
    all_products = Product.query.filter_by(creator=current_user).order_by(Product.product_name).all()
    products_data_for_display = [{'id': p.id, 'name': p.product_name} for p in all_products]
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
        electricity_cost_per_kwh=current_app.config['ELECTRICITY_COST_PER_KWH'],
        labor_cost_per_hour=current_app.config['LABOR_COST_PER_HOUR']
    )


# --- API 路由 ---

@bp.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
    
    # 執行產品總成本計算，這會返回包含食材成本細節的完整字典
    total_cost_details = product.calculate_total_product_cost(
        electricity_cost_per_kwh=current_app.config['ELECTRICITY_COST_PER_KWH'],
        labor_cost_per_hour=current_app.config['LABOR_COST_PER_HOUR']
    )
    
    # ★ 主要修改處：在回傳的 JSON 中加入 ingredient_cost_details
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
            'total_ingredient_cost': total_cost_details['total_ingredient_cost_for_recipe'],
            'servings_count': product.recipe.servings_count,
            # 新增的欄位：食材成本細節列表
            'ingredient_cost_details': total_cost_details['ingredient_cost_details']
        }
    })

# ... 其他 API 路由 (create, update, delete, search_recipes) 保持不變 ...
@bp.route('/api/create_product', methods=['POST'])
@login_required
def api_create_product():
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    recipe = Recipe.query.get(data.get('recipe_id'))
    if not recipe or recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '食譜不存在或無權限'}), 404
    
    # 後端重新計算成本以確保準確性
    temp_product = Product(
        recipe=recipe,
        batch_size=int(data.get('batch_size', 1)),
        bake_power_w=float(data.get('bake_power_w', 0)),
        bake_time_min=float(data.get('bake_time_min', 0)),
        production_time_hr=float(data.get('production_time_hr', 0)),
    )
    cost_data = temp_product.calculate_total_product_cost(
        electricity_cost_per_kwh=current_app.config['ELECTRICITY_COST_PER_KWH'],
        labor_cost_per_hour=current_app.config['LABOR_COST_PER_HOUR']
    )
    calculated_cost = cost_data['average_cost_per_product']
    
    try:
        product = Product(
            product_name=data.get('product_name'),
            description=data.get('description'),
            selling_price=float(data.get('selling_price', 0)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            creator=current_user,
            recipe=recipe,
            batch_size=temp_product.batch_size,
            bake_power_w=temp_product.bake_power_w,
            bake_time_min=temp_product.bake_time_min,
            production_time_hr=temp_product.production_time_hr,
            calculated_cost=calculated_cost # 使用後端計算的成本
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'產品「{product.product_name}」已成功建立！'})
    except (ValueError, TypeError) as e:
        return jsonify({'status': 'error', 'message': f'數據格式錯誤: {e}'}), 400

@bp.route('/api/products/<int:product_id>/update', methods=['POST'])
@login_required
def update_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
        
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    try:
        # 先更新產品的生產參數
        product.batch_size = int(data.get('batch_size', product.batch_size))
        product.bake_power_w = float(data.get('bake_power_w', product.bake_power_w))
        product.bake_time_min = float(data.get('bake_time_min', product.bake_time_min))
        product.production_time_hr = float(data.get('production_time_hr', product.production_time_hr))
        
        # 用更新後的參數，在後端重新計算成本
        cost_data = product.calculate_total_product_cost(
            electricity_cost_per_kwh=current_app.config['ELECTRICITY_COST_PER_KWH'],
            labor_cost_per_hour=current_app.config['LABOR_COST_PER_HOUR']
        )
        
        # 更新產品的其他資訊
        product.product_name = data.get('product_name', product.product_name)
        product.description = data.get('description', product.description)
        product.selling_price = float(data.get('selling_price', product.selling_price))
        product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
        product.calculated_cost = cost_data['average_cost_per_product'] # 儲存後端計算的成本

        db.session.commit()
        return jsonify({'status': 'success', 'message': '產品已成功更新！'})
    except (ValueError, TypeError) as e:
        return jsonify({'status': 'error', 'message': f'數據格式錯誤: {e}'}), 400

@bp.route('/api/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product_api(product_id):
    # ... 此函數保持不變 ...
    product = Product.query.get_or_404(product_id)
    if product.creator != current_user:
        return jsonify({'status': 'error', 'message': '無權限'}), 403
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({'status': 'success', 'message': '產品已成功刪除。'})

@bp.route('/api/get_recipe_details/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe_details(recipe_id):
    # ... 此函數保持不變 ...
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        return jsonify({'status': 'error', 'message': '無權限查看此食譜'}), 403
    
    recipe_data = recipe.calculate_nutrition()
    return jsonify({
        'status': 'success',
        'recipe_id': recipe.id,
        'recipe_name': recipe.recipe_name,
        'servings_count': recipe.servings_count,
        'total_ingredient_cost': recipe_data.get('total_ingredient_cost', 0),
        'ingredient_cost_details': recipe_data.get('ingredient_cost_details', [])
    })

