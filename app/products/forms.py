from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length, Optional

class ProductForm(FlaskForm):
    product_name = StringField('產品名稱', validators=[DataRequired(), Length(min=2, max=128)])
    description = TextAreaField('產品描述', validators=[Optional(), Length(max=500)])
    selling_price = FloatField('銷售價格', validators=[DataRequired(), NumberRange(min=0)], default=0)
    stock_quantity = IntegerField('庫存數量', validators=[DataRequired(), NumberRange(min=0)], default=0)
    
    # 新增的成本計算相關欄位
    batch_size = IntegerField('一次烤焙份數', validators=[DataRequired(), NumberRange(min=1)], default=1)
    bake_power_w = FloatField('烤箱功率 (瓦特)', validators=[DataRequired(), NumberRange(min=0)], default=0)
    bake_time_min = FloatField('烤焙時間 (分鐘)', validators=[DataRequired(), NumberRange(min=0)], default=0)
    production_time_hr = FloatField('單次製作時間 (小時)', validators=[DataRequired(), NumberRange(min=0)], default=0)

    submit = SubmitField('儲存產品')