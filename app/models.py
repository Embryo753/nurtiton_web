# app/models.py
# --- 100% 完整程式碼 ---
from datetime import datetime, timezone
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import func
import json
from sqlalchemy import desc

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    recipes = db.relationship('Recipe', back_populates='author', lazy='dynamic')
    products = db.relationship('Product', back_populates='creator', lazy='dynamic')
    ingredients = db.relationship('Ingredient', back_populates='creator', lazy='dynamic')
    orders = db.relationship('Order', back_populates='staff', lazy='dynamic')
    ingredient_prices = db.relationship('IngredientPrice', back_populates='user', lazy='dynamic')
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
    def __repr__(self): return f'<User {self.username}>'

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(128), nullable=False, index=True)
    source = db.Column(db.String(16), nullable=False, default='USER')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', back_populates='ingredients')
    tfda_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    cost_per_unit = db.Column(db.Float, nullable=False, default=0)
    unit_name = db.Column(db.String(16), default='g')
    prices = db.relationship('IngredientPrice', back_populates='ingredient', lazy='dynamic', cascade="all, delete-orphan")
    calories_kcal = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    saturated_fat_g = db.Column(db.Float, default=0)
    trans_fat_g = db.Column(db.Float, default=0)
    carbohydrate_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    sodium_mg = db.Column(db.Float, default=0)
    def __repr__(self): return f'<Ingredient {self.food_name}>'

class IngredientPrice(db.Model):
    __tablename__ = 'ingredient_prices'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(64), nullable=False, default='Manual')
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(16), nullable=False, default='g')
    purchase_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())

    ingredient = db.relationship('Ingredient', back_populates='prices')
    user = db.relationship('User', back_populates='ingredient_prices')

    def calculate_cost_per_gram(self):
        if self.quantity and self.quantity > 0:
            converted_quantity_base_unit = self.quantity
            unit_lower = self.unit.lower()
            
            if unit_lower == 'kg' or unit_lower == '公斤':
                converted_quantity_base_unit *= 1000
            elif unit_lower == 'l' or unit_lower == '公升':
                converted_quantity_base_unit *= 1000
            elif unit_lower == 'ml' or unit_lower == '毫升':
                pass
            
            return self.price / converted_quantity_base_unit
        return 0

    def __repr__(self):
        return f'<IngredientPrice {self.ingredient.food_name} - {self.price}/{self.quantity}{self.unit}>'


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    recipe_name = db.Column(db.String(128), index=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    serving_weight_g = db.Column(db.Float, default=100.0)
    final_weight_g = db.Column(db.Float, nullable=True)
    servings_count = db.Column(db.Integer, default=1)
    label_options = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', back_populates='recipes')
    ingredients = db.relationship('RecipeItem', back_populates='recipe', cascade="all, delete-orphan")
    def __repr__(self): return f'<Recipe {self.recipe_name}>'

    def calculate_nutrition(self):
        totals = {
            'calories_kcal': 0, 'protein_g': 0, 'fat_g': 0, 'carbohydrate_g': 0,
            'saturated_fat_g': 0, 'trans_fat_g': 0, 'sugar_g': 0, 'sodium_mg': 0,
            'total_weight_g': 0,
            'total_ingredient_cost': 0,
            'ingredient_cost_details': [],
            'has_trans_fat_non_art': False
        }

        if not self.ingredients:
            return totals

        for item in self.ingredients:
            current_ingredient_cost_per_gram = 0
            cost_source_info = "無價格紀錄"
            purchase_unit_info = ""

            # --- 修改處：從查詢最高價改為查詢「最新」的一筆價格 ---
            latest_price_entry = db.session.query(IngredientPrice).filter_by(
                ingredient_id=item.ingredient.id,
                user_id=self.user_id # 確保只查找登入使用者的價格
            ).order_by(
                desc(IngredientPrice.purchase_date) # 按購買日期降序排列
            ).first()

            if latest_price_entry:
                current_ingredient_cost_per_gram = latest_price_entry.calculate_cost_per_gram()
                cost_source_info = f"{latest_price_entry.source} ({latest_price_entry.purchase_date.strftime('%Y-%m-%d')})"
                purchase_unit_info = f"{latest_price_entry.unit}"
            else:
                # 如果沒有任何價格紀錄，則退回使用食材本身的預設成本
                current_ingredient_cost_per_gram = item.ingredient.cost_per_unit / 100.0
                cost_source_info = "預設成本"
                purchase_unit_info = f"{item.ingredient.unit_name}"

            scale = item.quantity_g / 100.0
            totals['calories_kcal'] += (item.ingredient.calories_kcal or 0) * scale
            totals['protein_g'] += (item.ingredient.protein_g or 0) * scale
            totals['fat_g'] += (item.ingredient.fat_g or 0) * scale
            totals['carbohydrate_g'] += (item.ingredient.carbohydrate_g or 0) * scale
            totals['saturated_fat_g'] += (item.ingredient.saturated_fat_g or 0) * scale
            totals['trans_fat_g'] += (item.ingredient.trans_fat_g or 0) * scale
            totals['sugar_g'] += (item.ingredient.sugar_g or 0) * scale
            totals['sodium_mg'] += (item.ingredient.sodium_mg or 0) * scale
            totals['total_weight_g'] += item.quantity_g

            if (item.ingredient.trans_fat_g or 0) > 0 and \
               any(keyword in item.ingredient.food_name for keyword in ['牛奶', '奶油', '乳', '牛油']):
                totals['has_trans_fat_non_art'] = True

            item_total_cost = current_ingredient_cost_per_gram * item.quantity_g
            totals['total_ingredient_cost'] += item_total_cost
            
            totals['ingredient_cost_details'].append({
                'ingredient_id': item.ingredient.id,
                'ingredient_name': item.ingredient.food_name,
                'quantity_g': item.quantity_g,
                'cost_per_gram': current_ingredient_cost_per_gram,
                'item_total_cost': item_total_cost,
                'cost_source': cost_source_info,
                'purchase_unit': purchase_unit_info
            })
        
        return totals

class RecipeItem(db.Model):
    __tablename__ = 'recipe_items'
    id = db.Column(db.Integer, primary_key=True)
    quantity_g = db.Column(db.Float, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    recipe = db.relationship('Recipe', back_populates='ingredients')
    ingredient = db.relationship('Ingredient')
    def __repr__(self): return f'<RecipeItem recipe:{self.recipe_id} ingredient:{self.ingredient_id} qty:{self.quantity_g}g>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(128), index=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    calculated_cost = db.Column(db.Float, default=0)
    selling_price = db.Column(db.Float, default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    creator = db.relationship('User', back_populates='products')
    recipe = db.relationship('Recipe')
    
    batch_size = db.Column(db.Integer, default=1)
    bake_power_w = db.Column(db.Float, default=0)
    bake_time_min = db.Column(db.Float, default=0)
    production_time_hr = db.Column(db.Float, default=0)
    
    def __repr__(self): return f'<Product {self.product_name}>'

    def calculate_total_product_cost(self, electricity_cost_per_kwh=3.0, labor_cost_per_hour=200.0):
        recipe_cost_details = self.recipe.calculate_nutrition()
        total_ingredient_cost_for_recipe = recipe_cost_details['total_ingredient_cost']

        ingredient_cost_per_serving = total_ingredient_cost_for_recipe / (self.recipe.servings_count or 1)

        electricity_cost_total = 0
        if self.bake_power_w and self.bake_time_min and self.bake_time_min > 0:
            total_bake_time_hr = self.bake_time_min / 60.0
            total_electricity_kwh = (self.bake_power_w * total_bake_time_hr) / 1000.0
            electricity_cost_total = total_electricity_kwh * electricity_cost_per_kwh
        
        labor_cost_total = 0
        if self.production_time_hr:
            labor_cost_total = self.production_time_hr * labor_cost_per_hour

        batch_ingredient_cost = (total_ingredient_cost_for_recipe / (self.recipe.servings_count or 1)) * (self.batch_size or 1)

        total_batch_cost = batch_ingredient_cost + electricity_cost_total + labor_cost_total

        average_cost_per_product = 0
        if self.batch_size and self.batch_size > 0:
            average_cost_per_product = total_batch_cost / self.batch_size
        
        return {
            'total_ingredient_cost_for_recipe': total_ingredient_cost_for_recipe,
            'ingredient_cost_details': recipe_cost_details['ingredient_cost_details'],
            'batch_ingredient_cost': batch_ingredient_cost,
            'electricity_cost_total': electricity_cost_total,
            'labor_cost_total': labor_cost_total,
            'total_batch_cost': total_batch_cost,
            'average_cost_per_product': average_cost_per_product
        }

    def calculate_profit_margin(self):
        if self.selling_price and self.selling_price > 0 and self.calculated_cost is not None:
            return ((self.selling_price - self.calculated_cost) / self.selling_price) * 100
        return 0

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    phone_number = db.Column(db.String(32), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    join_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')
    def __repr__(self): return f'<Customer {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default='completed')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    staff = db.relationship('User', back_populates='orders')
    customer = db.relationship('Customer', back_populates='orders')
    items = db.relationship('OrderItem', backref='order', cascade="all, delete-orphan")
    def __repr__(self): return f'<Order {self.id}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_sale = db.Column(db.Float, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product')
    def __repr__(self): return f'<OrderItem order:{self.order_id} product:{self.product_id} qty:{self.quantity}>'
