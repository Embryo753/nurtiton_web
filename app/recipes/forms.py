# --- 100% 完整程式碼 ---

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange

class RecipeForm(FlaskForm):
    recipe_name = StringField('食譜名稱', validators=[DataRequired(), Length(min=2, max=128)])
    submit = SubmitField('建立食譜')

class IngredientForm(FlaskForm):
    # --- 關鍵修正：加入 Meta 內部類別，並設定 csrf = False ---
    class Meta:
        csrf = False

    food_name = StringField('食材名稱', validators=[DataRequired(), Length(min=1, max=128)])
    calories_kcal = FloatField('熱量 (大卡/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    protein_g = FloatField('蛋白質 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    fat_g = FloatField('總脂肪 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    saturated_fat_g = FloatField('飽和脂肪 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    trans_fat_g = FloatField('反式脂肪 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    carbohydrate_g = FloatField('總碳水化合物 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    sugar_g = FloatField('糖 (克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])
    sodium_mg = FloatField('鈉 (毫克/100g)', validators=[InputRequired(message="此欄位不可空白"), NumberRange(min=0)])