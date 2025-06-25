# app/recipes/routes.py (重構後)
from flask import render_template, flash, redirect, url_for, abort, jsonify, request, current_app
import json
from datetime import datetime, timezone
from app import db
from app.recipes import bp
from flask_login import login_required, current_user
from app.models import Recipe, Ingredient, RecipeItem, Product
from app.recipes.forms import RecipeForm, IngredientForm

# --- 新增的輔助函數 ---
def _generate_label_data(recipe_obj):
    """
    輔助函數，用於計算並格式化營養標示資料。
    它接受一個 Recipe 物件 (無論是來自資料庫還是臨時建立的)。
    返回一個包含標籤所需文字的字典。
    """
    # 1. 執行核心計算
    raw_totals = recipe_obj.calculate_nutrition()

    # 2. 確定最終重量和份數
    final_weight = recipe_obj.final_weight_g if recipe_obj.final_weight_g and recipe_obj.final_weight_g > 0 else raw_totals.get('total_weight_g', 0)
    servings_count = recipe_obj.servings_count if recipe_obj.servings_count and recipe_obj.servings_count > 0 else 1
    serving_weight = final_weight / servings_count if servings_count > 0 and final_weight > 0 else 0

    # 3. 計算營養密度
    density = {}
    if final_weight > 0:
        for key, value in raw_totals.items():
            if isinstance(value, (int, float)) and key != 'total_cost':
                density[key] = value / final_weight
    
    per_serving = {key: val * serving_weight for key, val in density.items()}
    per_100g = {key: val * 100 for key, val in density.items()}

    # 4. 格式化成分字串 (按重量降序排列)
    ingredients_list_sorted = sorted(recipe_obj.ingredients, key=lambda item: item.quantity_g, reverse=True)
    ingredients_str = "、".join([item.ingredient.food_name for item in ingredients_list_sorted])

    # 5. 處理標籤顯示選項
    label_options = recipe_obj.label_options or {}
    show_options = label_options.get('show_nutrients', {
        'calories_kcal': True, 'protein_g': True, 'fat_g': True,
        'saturated_fat_g': True, 'trans_fat_g': True, 'carbohydrate_g': True,
        'sugar_g': True, 'sodium_mg': True
    })

    # 6. 產生營養標示表格的文字
    nutrition_lines = []
    if show_options.get('calories_kcal', True):
        nutrition_lines.append(f"熱量          {per_serving.get('calories_kcal', 0):>7.1f} 大卡 {per_100g.get('calories_kcal', 0):>9.1f} 大卡")
    if show_options.get('protein_g', True):
        nutrition_lines.append(f"蛋白質        {per_serving.get('protein_g', 0):>7.1f} 公克 {per_100g.get('protein_g', 0):>9.1f} 公克")
    if show_options.get('fat_g', True):
        nutrition_lines.append(f"脂肪          {per_serving.get('fat_g', 0):>7.1f} 公克 {per_100g.get('fat_g', 0):>9.1f} 公克")
    if show_options.get('saturated_fat_g', True):
        nutrition_lines.append(f"  飽和脂肪    {per_serving.get('saturated_fat_g', 0):>7.1f} 公克 {per_100g.get('saturated_fat_g', 0):>9.1f} 公克")
    if show_options.get('trans_fat_g', True):
        nutrition_lines.append(f"  反式脂肪    {per_serving.get('trans_fat_g', 0):>7.1f} 公克 {per_100g.get('trans_fat_g', 0):>9.1f} 公克")
    if show_options.get('carbohydrate_g', True):
        nutrition_lines.append(f"碳水化合物    {per_serving.get('carbohydrate_g', 0):>7.1f} 公克 {per_100g.get('carbohydrate_g', 0):>9.1f} 公克")
    if show_options.get('sugar_g', True):
        nutrition_lines.append(f"  糖          {per_serving.get('sugar_g', 0):>7.1f} 公克 {per_100g.get('sugar_g', 0):>9.1f} 公克")
    if show_options.get('sodium_mg', True):
        # 修正：鈉含量(mg)通常顯示為整數
        nutrition_lines.append(f"鈉            {per_serving.get('sodium_mg', 0):>7.0f} 毫克 {per_100g.get('sodium_mg', 0):>9.0f} 毫克")
    
    nutrition_str = (
        f"--- 每份 {serving_weight:.1f} 公克 ---\n"
        f"本包裝含 {servings_count} 份\n"
        f"\n"
        f"              每份      每100公克\n" +
        "\n".join(nutrition_lines)
    )

    # 7. 格式化過敏原字串
    allergens = label_options.get('allergens', [])
    allergen_text = ""
    if allergens:
        allergen_text = "本產品含有" + "、".join(allergens) + "及其製品，不適合對其過敏體質者食用。"

    # 8. 回傳最終的字典
    return {
        'product_name': recipe_obj.recipe_name,
        'ingredients': ingredients_str,
        'net_weight': f"{final_weight:.1f} 公克",
        'nutrition': nutrition_str,
        'allergens': allergen_text,
        'has_trans_fat_non_art': raw_totals.get('has_trans_fat_non_art', False)
    }
# --- 輔助函數結束 ---


@bp.route('/')
@login_required
def index():
    recipes = Recipe.query.filter_by(author=current_user).order_by(Recipe.updated_at.desc()).all()
    return render_template('recipes/index.html', title='我的食譜', recipes=recipes)


@bp.route('/create', methods=['POST'])
@login_required
def create_and_redirect():
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    recipe = Recipe(recipe_name=f"未命名食譜 {timestamp}", author=current_user)
    db.session.add(recipe)
    db.session.commit()
    flash('已建立新食譜，請開始編輯。')
    return redirect(url_for('recipes.recipe_detail', recipe_id=recipe.id))


@bp.route('/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)

    linked_product = Product.query.filter_by(recipe_id=recipe.id).first()
    if linked_product:
        flash(f'無法刪除食譜 "{recipe.recipe_name}"，因為它已被產品 "{linked_product.product_name}" 使用。請先刪除關聯的產品。', 'danger')
        return redirect(url_for('recipes.index'))
    
    recipe_name = recipe.recipe_name
    db.session.delete(recipe)
    db.session.commit()
    flash(f'食譜 "{recipe_name}" 已成功刪除。', 'success')
    return redirect(url_for('recipes.index'))


@bp.route('/<int:recipe_id>')
@login_required
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    
    initial_state = {
        'ingredients': [],
        'serving_weight_g': recipe.serving_weight_g,
        'servings_count': recipe.servings_count,
        'final_weight_g': recipe.final_weight_g or '',
        'label_options': recipe.label_options or {}
    }
    for item in recipe.ingredients:
        initial_state['ingredients'].append({
            'ingredient_id': item.ingredient.id,
            'ingredient_name': item.ingredient.food_name,
            'quantity_g': item.quantity_g,
            'details': {
                'calories_kcal': item.ingredient.calories_kcal, 'protein_g': item.ingredient.protein_g,
                'fat_g': item.ingredient.fat_g, 'carbohydrate_g': item.ingredient.carbohydrate_g,
                'saturated_fat_g': item.ingredient.saturated_fat_g, 'trans_fat_g': item.ingredient.trans_fat_g,
                'sugar_g': item.ingredient.sugar_g, 'sodium_mg': item.ingredient.sodium_mg,
                'cost_per_unit': item.ingredient.cost_per_unit,
                'unit_name': item.ingredient.unit_name
            }
        })
    return render_template('recipes/recipe_detail.html', title=f"編輯食譜: {recipe.recipe_name}", recipe=recipe, initial_state=initial_state)


@bp.route('/<int:recipe_id>/label')
@login_required
def recipe_label(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)

    # 使用重構後的輔助函數來產生標籤資料
    final_texts = _generate_label_data(recipe)
    
    # 提取 'has_trans_fat_non_art' 資訊給模板使用
    recipe_calculated_data = {'has_trans_fat_non_art': final_texts.pop('has_trans_fat_non_art', False)}

    return render_template(
        'recipes/label.html',
        recipe=recipe,
        final_texts=final_texts,
        recipe_calculated_data=recipe_calculated_data
    )


@bp.route('/ingredients', methods=['GET'])
@login_required
def manage_ingredients():
    return render_template('recipes/manage_ingredients.html', title='食材管理')


# --- API 路由 ---

@bp.route('/api/ingredient/<int:ingredient_id>')
@login_required
def get_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.creator != current_user:
        return jsonify({'status': 'error', 'message': '權限不足'}), 403
    ingredient_data = {
        'id': ingredient.id, 'food_name': ingredient.food_name,
        'calories_kcal': ingredient.calories_kcal, 'protein_g': ingredient.protein_g,
        'fat_g': ingredient.fat_g, 'saturated_fat_g': ingredient.saturated_fat_g,
        'trans_fat_g': ingredient.trans_fat_g, 'carbohydrate_g': ingredient.carbohydrate_g,
        'sugar_g': ingredient.sugar_g, 'sodium_mg': ingredient.sodium_mg,
        'cost_per_unit': ingredient.cost_per_unit,
        'unit_name': ingredient.unit_name
    }
    return jsonify({'status': 'success', 'data': ingredient_data})


@bp.route('/api/ingredient/create', methods=['POST'])
@login_required
def create_ingredient_api():
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400
    existing_ingredient = Ingredient.query.filter_by(food_name=data.get('food_name'), creator=current_user).first()
    if existing_ingredient: return jsonify({'status': 'error', 'message': f"名稱「{data.get('food_name')}」已被使用，請換一個。"}), 400
    form = IngredientForm(data=data)
    if form.validate():
        ingredient = Ingredient(creator=current_user, source='USER')
        form.populate_obj(ingredient)
        db.session.add(ingredient)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '食材已成功新增！', 'ingredient': {'id': ingredient.id, 'name': ingredient.food_name}})
    else:
        return jsonify({'status': 'error', 'message': '資料驗證失敗', 'errors': form.errors}), 422


@bp.route('/api/ingredient/<int:ingredient_id>/update', methods=['POST'])
@login_required
def update_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.creator != current_user: return jsonify({'status': 'error', 'message': '權限不足'}), 403
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400
    new_name = data.get('food_name')
    existing_ingredient = Ingredient.query.filter(Ingredient.id != ingredient_id, Ingredient.food_name == new_name, Ingredient.creator == current_user).first()
    if existing_ingredient: return jsonify({'status': 'error', 'message': f'名稱「{new_name}」已被其他食材使用，請換一個。'}), 400
    form = IngredientForm(data=data)
    if form.validate():
        form.populate_obj(ingredient)
        db.session.commit()
        return jsonify({'status': 'success', 'message': '食材已成功更新！', 'ingredient': {'id': ingredient.id, 'name': ingredient.food_name}})
    else:
        return jsonify({'status': 'error', 'message': '資料驗證失敗', 'errors': form.errors}), 422


@bp.route('/api/ingredient/<int:ingredient_id>/delete', methods=['POST'])
@login_required
def delete_ingredient_api(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.creator != current_user: return jsonify({'status': 'error', 'message': '權限不足'}), 403
    ingredient_name = ingredient.food_name
    db.session.delete(ingredient)
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'食材「{ingredient_name}」已成功刪除。'})


@bp.route('/api/search_ingredients')
@login_required
def search_ingredients():
    query = request.args.get('q', '', type=str)
    source_filter = request.args.get('source', 'ALL', type=str)
    base_query = Ingredient.query
    if source_filter == 'USER':
        base_query = base_query.filter(Ingredient.creator == current_user)
    elif source_filter == 'TFDA':
        base_query = base_query.filter_by(source='TFDA')
    if query:
        search = f"%{query}%"
        base_query = base_query.filter(Ingredient.food_name.like(search))
    ingredients = base_query.order_by(Ingredient.food_name).limit(20).all()
    results = [{'id': ing.id, 'name': ing.food_name,
                'calories_kcal': ing.calories_kcal, 'protein_g': ing.protein_g,
                'fat_g': ing.fat_g, 'carbohydrate_g': ing.carbohydrate_g,
                'saturated_fat_g': ing.saturated_fat_g, 'trans_fat_g': ing.trans_fat_g,
                'sugar_g': ing.sugar_g, 'sodium_mg': ing.sodium_mg,
                'cost_per_unit': ing.cost_per_unit,
                'unit_name': ing.unit_name
                } for ing in ingredients]
    return jsonify(results)


@bp.route('/api/recipe/<int:recipe_id>/save', methods=['POST'])
@login_required
def save_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user: return jsonify({'status': 'error', 'message': '權限不足'}), 403
    data = request.get_json()
    if not data: return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400
    recipe.recipe_name = data.get('recipe_name', recipe.recipe_name)
    recipe.serving_weight_g = float(data.get('serving_weight_g', 100))
    recipe.servings_count = int(data.get('servings_count', 1))
    final_weight_str = data.get('final_weight_g')
    try:
        recipe.final_weight_g = float(final_weight_str) if final_weight_str and float(final_weight_str) > 0 else None
    except (ValueError, TypeError):
        recipe.final_weight_g = None
    recipe.label_options = data.get('label_options', {})
    
    RecipeItem.query.filter_by(recipe_id=recipe.id).delete()
    for item_data in data.get('ingredients', []):
        ingredient = Ingredient.query.get(item_data['ingredient_id'])
        if ingredient and float(item_data['quantity_g']) > 0:
            recipe_item = RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity_g=float(item_data['quantity_g']))
            db.session.add(recipe_item)
            
    db.session.commit()
    return jsonify({'status': 'success', 'message': '食譜已成功儲存！'})


@bp.route('/api/recipe/preview_label', methods=['POST'])
@login_required
def preview_label():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    try:
        final_weight_str = data.get('final_weight_g')
        final_weight_val = float(final_weight_str) if final_weight_str else None

        # 建立一個臨時的、僅存在於記憶體中的 Recipe 物件用於計算
        temp_recipe = Recipe(
            recipe_name=data.get('recipe_name', '預覽食譜'),
            final_weight_g=final_weight_val,
            servings_count=int(data.get('servings_count', 1)),
            label_options=data.get('label_options', {})
        )
        
        # 填充臨時的食材項目
        for item_data in data.get('ingredients', []):
            ingredient = Ingredient.query.get(item_data['ingredient_id'])
            if ingredient and float(item_data['quantity_g']) > 0:
                temp_recipe_item = RecipeItem(ingredient=ingredient, quantity_g=float(item_data['quantity_g']))
                temp_recipe.ingredients.append(temp_recipe_item)
        
        # 使用重構後的輔助函數來產生標籤資料
        label_data = _generate_label_data(temp_recipe)
        
        # API 不需要回傳這個內部欄位
        label_data.pop('has_trans_fat_non_art', None) 
        
        # 修改成分和淨重的格式以符合 API 回傳的期望
        label_data['ingredients'] = "成分：" + label_data['ingredients']
        label_data['net_weight'] = "淨重：" + label_data['net_weight']

        return jsonify({'status': 'success', **label_data})

    except Exception as e:
        current_app.logger.error(f"Error during label preview generation: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'產生預覽時發生內部錯誤: {e}'}), 500
