from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class ProductForm(FlaskForm):
    product_name = StringField('產品名稱', validators=[DataRequired(), Length(min=2, max=128)])
    description = TextAreaField('產品描述', validators=[Optional(), Length(max=500)])
    selling_price = FloatField('銷售價格', validators=[DataRequired(), NumberRange(min=0)], default=0)
    stock_quantity = IntegerField('庫存數量', validators=[DataRequired(), NumberRange(min=0)], default=0)
    submit = SubmitField('儲存產品')