# --- 100% 完整程式碼 ---
from datetime import datetime, timezone
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import func

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
    calories_kcal = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    fat_g = db.Column(db.Float, default=0)
    saturated_fat_g = db.Column(db.Float, default=0)
    trans_fat_g = db.Column(db.Float, default=0)
    carbohydrate_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    sodium_mg = db.Column(db.Float, default=0)
    def __repr__(self): return f'<Ingredient {self.food_name}>'

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    recipe_name = db.Column(db.String(128), index=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    serving_weight_g = db.Column(db.Float, default=100.0)
    final_weight_g = db.Column(db.Float, nullable=True)
    servings_count = db.Column(db.Integer, default=1)
    label_options = db.Column(db.JSON) # <-- 新增此欄位
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', back_populates='recipes')
    ingredients = db.relationship('RecipeItem', back_populates='recipe', cascade="all, delete-orphan")
    def __repr__(self): return f'<Recipe {self.recipe_name}>'
    def calculate_nutrition(self):
        totals = {'calories_kcal': 0, 'protein_g': 0, 'fat_g': 0, 'carbohydrate_g': 0, 'saturated_fat_g': 0, 'trans_fat_g': 0, 'sugar_g': 0, 'sodium_mg': 0, 'total_weight_g': 0}
        if not self.ingredients: return totals
        for item in self.ingredients:
            scale = item.quantity_g / 100.0
            totals['calories_kcal'] += item.ingredient.calories_kcal * scale
            totals['protein_g'] += item.ingredient.protein_g * scale
            totals['fat_g'] += item.ingredient.fat_g * scale
            totals['carbohydrate_g'] += item.ingredient.carbohydrate_g * scale
            totals['saturated_fat_g'] += item.ingredient.saturated_fat_g * scale
            totals['trans_fat_g'] += item.ingredient.trans_fat_g * scale
            totals['sugar_g'] += item.ingredient.sugar_g * scale
            totals['sodium_mg'] += item.ingredient.sodium_mg * scale
            totals['total_weight_g'] += item.quantity_g
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
    def __repr__(self): return f'<Product {self.product_name}>'

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