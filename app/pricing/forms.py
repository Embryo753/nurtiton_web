# app/pricing/forms.py
from flask_wtf import FlaskForm
# 移除 QuerySelectField，新增 StringField
from wtforms import FloatField, IntegerField, SelectField, SubmitField, FileField, StringField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
# from wtforms_sqlalchemy.fields import QuerySelectField # 移除此行
# from app.models import Ingredient # 這裡可以暫時保留或移除，因為不再直接用於QuerySelectField
from flask_login import current_user
# from flask import current_app # 移除此行，因為get_user_ingredients_query不再需要

# 移除 get_user_ingredients_query 輔助函數

class IngredientPriceForm(FlaskForm):
    # 將 ingredient 欄位從 QuerySelectField 改為 StringField
    ingredient_name = StringField(
        '食材名稱',
        validators=[DataRequired('請輸入食材名稱'), Length(min=1, max=128)]
    )
    source = SelectField(
        '來源',
        choices=[
            ('Manual', '手動輸入'),
            ('PX Mart', '全聯福利中心'),
            ('Carrefour', '家樂福超市'),
            ('Shopee', '蝦皮購物')
        ],
        validators=[DataRequired('請選擇價格來源')]
    )
    price = FloatField('購買價格 (NT$)', validators=[DataRequired(), NumberRange(min=0.01)])
    quantity = FloatField('購買總數量', validators=[DataRequired(), NumberRange(min=0.001)])
    unit = StringField('數量單位 (例如: g, ml, 個, 包)', validators=[DataRequired(), Length(max=16)])
    submit = SubmitField('新增價格紀錄')

class UploadPriceForm(FlaskForm):
    csv_file = FileField('上傳 CSV/Excel 檔案', validators=[DataRequired()])
    submit = SubmitField('匯入價格')