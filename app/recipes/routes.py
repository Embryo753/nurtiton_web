from flask import render_template, flash, redirect, url_for, abort, jsonify, request, current_app
import json
from datetime import datetime, timezone
from app import db
from app.recipes import bp
from flask_login import login_required, current_user
from app.models import Recipe, Ingredient, RecipeItem
from app.recipes.forms import RecipeForm, IngredientForm

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
            'ingredient_id': item.ingredient.id, 'ingredient_name': item.ingredient.food_name, 'quantity_g': item.quantity_g,
            'details': {
                'calories_kcal': item.ingredient.calories_kcal, 'protein_g': item.ingredient.protein_g,
                'fat_g': item.ingredient.fat_g, 'carbohydrate_g': item.ingredient.carbohydrate_g,
                'saturated_fat_g': item.ingredient.saturated_fat_g, 'trans_fat_g': item.ingredient.trans_fat_g,
                'sugar_g': item.ingredient.sugar_g, 'sodium_mg': item.ingredient.sodium_mg
            }
        })
    return render_template('recipes/recipe_detail.html', title=f"編輯食譜: {recipe.recipe_name}", recipe=recipe, initial_state=initial_state)

# =====================================================================
# VVVVVV 這是唯一被修改的函式 VVVVVV
# =====================================================================
@bp.route('/<int:recipe_id>/label', methods=['GET', 'POST'])
@login_required
def recipe_label(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)

    if request.method == 'POST':
        # 從前端提交的隱藏表單中，直接獲取編輯過的文字
        final_texts = {
            'product_name': request.form.get('product_name'),
            'ingredients': request.form.get('ingredients'),
            'net_weight': request.form.get('net_weight'),
            'nutrition': request.form.get('nutrition'),
            'allergens': request.form.get('allergens')
        }
        # 使用這些已編輯的文字來渲染最終的標籤頁面
        return render_template(
            'recipes/label.html',
            recipe=recipe,
            final_texts=final_texts
        )
    
    # 如果是 GET 請求，維持原有功能，從資料庫即時計算
    else:
        raw_totals = recipe.calculate_nutrition()
        final_weight = recipe.final_weight_g if recipe.final_weight_g and recipe.final_weight_g > 0 else raw_totals.get('total_weight_g', 0)
        servings_count = recipe.servings_count if recipe.servings_count > 0 else 1
        serving_weight = final_weight / servings_count if servings_count > 0 else 0
        
        density = {}
        if final_weight > 0:
            for key, value in raw_totals.items():
                if isinstance(value, (int, float)):
                    density[key] = value / final_weight
        
        per_serving = {key: val * serving_weight for key, val in density.items()}
        per_100g = {key: val * 100 for key, val in density.items()}
        
        ingredients_list_sorted = sorted(recipe.ingredients, key=lambda item: item.quantity_g, reverse=True)
        ingredients_str = "成分：" + "、".join([item.ingredient.food_name for item in ingredients_list_sorted])

        nutrition_str = (
            f"--- 每份 {serving_weight:.1f} 公克 ---\n"
            f"本包裝含 {servings_count} 份\n"
            f"\n"
            f"                      每份      每100公克\n"
            f"熱量        {per_serving.get('calories_kcal', 0):>7.1f} 大卡 {per_100g.get('calories_kcal', 0):>9.1f} 大卡\n"
            f"蛋白質      {per_serving.get('protein_g', 0):>7.1f} 公克 {per_100g.get('protein_g', 0):>9.1f} 公克\n"
            f"脂肪        {per_serving.get('fat_g', 0):>7.1f} 公克 {per_100g.get('fat_g', 0):>9.1f} 公克\n"
            f"  飽和脂肪  {per_serving.get('saturated_fat_g', 0):>7.1f} 公克 {per_100g.get('saturated_fat_g', 0):>9.1f} 公克\n"
            f"  反式脂肪  {per_serving.get('trans_fat_g', 0):>7.1f} 公克 {per_100g.get('trans_fat_g', 0):>9.1f} 公克\n"
            f"碳水化合物  {per_serving.get('carbohydrate_g', 0):>7.1f} 公克 {per_100g.get('carbohydrate_g', 0):>9.1f} 公克\n"
            f"  糖        {per_serving.get('sugar_g', 0):>7.1f} 公克 {per_100g.get('sugar_g', 0):>9.1f} 公克\n"
            f"鈉          {per_serving.get('sodium_mg', 0):>7.1f} 毫克 {per_100g.get('sodium_mg', 0):>9.1f} 毫克"
        )
        
        label_options = recipe.label_options or {}
        allergens = label_options.get('allergens', [])
        allergen_text = ""
        if allergens:
            allergen_text = "本產品含有" + "、".join(allergens) + "及其製品，不適合對其過敏體質者食用。"

        # 為了讓模板能統一處理，這裡也建立一個同結構的字典
        final_texts = {
             'product_name': recipe.recipe_name,
             'ingredients': ingredients_str,
             'net_weight': f"淨重：{final_weight:.1f} 公克",
             'nutrition': nutrition_str,
             'allergens': allergen_text
        }

        return render_template(
            'recipes/label.html',
            recipe=recipe,
            final_texts=final_texts
        )
# =====================================================================
# ^^^^^^ 以上是唯一被修改的函式，以下所有函式都與您最初的版本相同 ^^^^^^
# =====================================================================


@bp.route('/ingredients', methods=['GET'])
@login_required
def manage_ingredients():
    return render_template('recipes/manage_ingredients.html', title='食材管理')

@bp.route('/api/ingredient/<int:ingredient_id>')
@login_required
def get_ingredient(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.creator != current_user: return jsonify({'status': 'error', 'message': '權限不足'}), 403
    ingredient_data = {'id': ingredient.id, 'food_name': ingredient.food_name, 'calories_kcal': ingredient.calories_kcal, 'protein_g': ingredient.protein_g, 'fat_g': ingredient.fat_g, 'saturated_fat_g': ingredient.saturated_fat_g, 'trans_fat_g': ingredient.trans_fat_g, 'carbohydrate_g': ingredient.carbohydrate_g, 'sugar_g': ingredient.sugar_g, 'sodium_mg': ingredient.sodium_mg}
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
    results = [{'id': ing.id, 'name': ing.food_name, 'calories_kcal': ing.calories_kcal, 'protein_g': ing.protein_g, 'fat_g': ing.fat_g, 'carbohydrate_g': ing.carbohydrate_g, 'saturated_fat_g': ing.saturated_fat_g, 'trans_fat_g': ing.trans_fat_g, 'sugar_g': ing.sugar_g, 'sodium_mg': ing.sodium_mg } for ing in ingredients]
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
    final_weight = data.get('final_weight_g')
    recipe.final_weight_g = float(final_weight) if final_weight and float(final_weight) > 0 else None
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
    """
    接收前端的即時食譜資料，回傳計算好的標籤文字 (JSON格式)。
    此函式不會寫入資料庫，僅用於即時預覽。
    """
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': '請求資料不完整'}), 400

    try:
        # 1. 在記憶體中建立一個暫時的 Recipe 物件來存放前端資料
        temp_recipe = Recipe(
            recipe_name=data.get('recipe_name', '預覽食譜'),
            final_weight_g=float(data['final_weight_g']) if data.get('final_weight_g') else None,
            servings_count=int(data.get('servings_count', 1)),
            label_options=data.get('label_options', {})
        )

        # 2. 建立暫時的 RecipeItem 物件列表
        for item_data in data.get('ingredients', []):
            ingredient = Ingredient.query.get(item_data['ingredient_id'])
            if ingredient and float(item_data['quantity_g']) > 0:
                # 將暫時的 RecipeItem 加入暫時的 Recipe 中
                temp_recipe.ingredients.append(
                    RecipeItem(ingredient=ingredient, quantity_g=float(item_data['quantity_g']))
                )

        # 3. 呼叫您在模型中已有的計算方法，重複利用現有邏輯！
        raw_totals = temp_recipe.calculate_nutrition()
        
        # 4. 執行與您 recipe_label 路由中完全相同的後續計算
        final_weight = temp_recipe.final_weight_g if temp_recipe.final_weight_g and temp_recipe.final_weight_g > 0 else raw_totals.get('total_weight_g', 0)
        servings_count = temp_recipe.servings_count if temp_recipe.servings_count > 0 else 1
        serving_weight = final_weight / servings_count if servings_count > 0 else 0
        
        density = {}
        if final_weight > 0:
            for key, value in raw_totals.items():
                if isinstance(value, (int, float)):
                    density[key] = value / final_weight
        
        per_serving = {key: val * serving_weight for key, val in density.items()}
        per_100g = {key: val * 100 for key, val in density.items()}

        # 5. 格式化最終要顯示的文字字串
        ingredients_list_sorted = sorted(temp_recipe.ingredients, key=lambda item: item.quantity_g, reverse=True)
        ingredients_str = "、".join([item.ingredient.food_name for item in ingredients_list_sorted])

        # 您可以自由修改此處的文字排版格式
        nutrition_str = (
            f"--- 每份 {serving_weight:.1f} 公克 ---\n"
            f"本包裝含 {servings_count} 份\n"
            f"\n"
            f"                      每份      每100公克\n"
            f"熱量        {per_serving.get('calories_kcal', 0):>7.1f} 大卡 {per_100g.get('calories_kcal', 0):>9.1f} 大卡\n"
            f"蛋白質      {per_serving.get('protein_g', 0):>7.1f} 公克 {per_100g.get('protein_g', 0):>9.1f} 公克\n"
            f"脂肪        {per_serving.get('fat_g', 0):>7.1f} 公克 {per_100g.get('fat_g', 0):>9.1f} 公克\n"
            f"  飽和脂肪  {per_serving.get('saturated_fat_g', 0):>7.1f} 公克 {per_100g.get('saturated_fat_g', 0):>9.1f} 公克\n"
            f"  反式脂肪  {per_serving.get('trans_fat_g', 0):>7.1f} 公克 {per_100g.get('trans_fat_g', 0):>9.1f} 公克\n"
            f"碳水化合物  {per_serving.get('carbohydrate_g', 0):>7.1f} 公克 {per_100g.get('carbohydrate_g', 0):>9.1f} 公克\n"
            f"  糖        {per_serving.get('sugar_g', 0):>7.1f} 公克 {per_100g.get('sugar_g', 0):>9.1f} 公克\n"
            f"鈉          {per_serving.get('sodium_mg', 0):>7.1f} 毫克 {per_100g.get('sodium_mg', 0):>9.1f} 毫克"
        )
        
        # 這裡您可以加入更複雜的過敏原邏輯
        allergens_str = "過敏原資訊：本產品含有牛奶、蛋及其製品。"

        # 6. 將結果包裝成 JSON 回傳給前端
        return jsonify({
            'status': 'success',
            'product_name': temp_recipe.recipe_name,
            'ingredients': "成分：" + ingredients_str,
            'net_weight': f"淨重：{final_weight:.1f} 公克",
            'nutrition': nutrition_str,
            'allergens': allergens_str
        })

    except Exception as e:
        current_app.logger.error(f"Error during label preview generation: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': f'產生預覽時發生內部錯誤: {e}'}), 500