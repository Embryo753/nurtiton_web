from flask import render_template, flash, redirect, url_for, abort, jsonify, request
from app import db
from app.products import bp
from flask_login import login_required, current_user
from app.models import Product, Recipe # 匯入 Product 和 Recipe 模型
from app.products.forms import ProductForm # 匯入 ProductForm
from datetime import datetime, timezone

@bp.route('/')
@login_required
def index():
    # 查詢目前使用者建立的所有產品，並依更新時間降冪排序
    products = Product.query.filter_by(creator=current_user).order_by(Product.updated_at.desc()).all()
    return render_template('products/index.html', title='產品管理', products=products)

@bp.route('/create/<int:recipe_id>', methods=['GET', 'POST'])
@login_required
def create_from_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # 確保只有食譜的作者才能從該食譜建立產品
    if recipe.author != current_user:
        abort(403) # 如果不是作者，返回 403 Forbidden 錯誤

    # 調用食譜的 calculate_nutrition 方法來獲取總成本
    nutrition_totals = recipe.calculate_nutrition()
    calculated_cost = nutrition_totals['total_cost']

    # 預設產品名稱為食譜名稱加上 "(產品)"
    default_product_name = recipe.recipe_name + " (產品)"

    # 初始化表單，並預設一些值
    form = ProductForm(
        product_name=default_product_name,
        selling_price=round(calculated_cost * 1.5, 2), # 預設售價為成本的1.5倍，並四捨五入到小數點後兩位
        stock_quantity=0 # 預設庫存為0
    )

    # 如果表單提交且驗證通過
    if form.validate_on_submit():
        product = Product(
            product_name=form.product_name.data,
            description=form.description.data,
            calculated_cost=calculated_cost, # 儲存計算出的成本
            selling_price=form.selling_price.data,
            stock_quantity=form.stock_quantity.data,
            creator=current_user, # 產品的建立者為當前登入使用者
            recipe=recipe # 將產品與食譜關聯
        )
        db.session.add(product)
        db.session.commit()
        flash(f'產品 "{product.product_name}" 已成功建立！')
        return redirect(url_for('products.index')) # 建立成功後導向產品列表頁

    # 如果是 GET 請求或者表單驗證失敗，渲染創建頁面
    return render_template(
        'products/create_product.html',
        title=f'從食譜 "{recipe.recipe_name}" 建立產品',
        form=form,
        recipe=recipe,
        calculated_cost=calculated_cost # 將計算出的成本傳遞給模板顯示
    )

@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    # 確保只有產品的建立者才能編輯該產品
    if product.creator != current_user:
        abort(403)

    # 重新計算食譜成本，確保是最新的
    # 這樣即使食譜內容有變更，產品成本也能保持最新
    nutrition_totals = product.recipe.calculate_nutrition()
    recalculated_cost = nutrition_totals['total_cost']
    
    # 如果產品的 calculated_cost 和重新計算的成本不一致，則更新
    # 這裡可以選擇是否立即提交，或者在表單提交時統一提交
    if product.calculated_cost != recalculated_cost:
        product.calculated_cost = recalculated_cost
        db.session.commit() # 立即提交更新的成本

    # 初始化表單，並用現有產品數據填充
    form = ProductForm(obj=product)

    # 如果表單提交且驗證通過
    if form.validate_on_submit():
        form.populate_obj(product) # 將表單數據填充到產品物件
        product.calculated_cost = recalculated_cost # 再次確認使用最新的成本
        product.updated_at = datetime.now(timezone.utc) # 更新修改時間
        db.session.commit()
        flash(f'產品 "{product.product_name}" 已成功更新！')
        return redirect(url_for('products.index')) # 更新成功後導向產品列表頁
    
    # 將 recalculated_cost 傳遞給模板顯示
    return render_template(
        'products/edit_product.html',
        title=f'編輯產品: {product.product_name}',
        form=form,
        product=product,
        recalculated_cost=recalculated_cost # 將重新計算的成本傳遞給模板顯示
    )

@bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # 確保只有產品的建立者才能刪除該產品
    if product.creator != current_user:
        abort(403)
    
    product_name = product.product_name
    db.session.delete(product) # 從資料庫中刪除產品
    db.session.commit()
    flash(f'產品 "{product_name}" 已成功刪除。')
    return redirect(url_for('products.index')) # 刪除成功後導向產品列表頁