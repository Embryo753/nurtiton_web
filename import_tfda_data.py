# --- 100% 完整程式碼 (最終版 v4 - 正確欄位對應版) ---

import requests
import pandas as pd
import sqlite3
from datetime import datetime, timezone

TFDA_API_URL = "https://data.fda.gov.tw/opendata/exportDataList.do?method=openData&InfoId=20"
DB_FILE = 'app.db'

def import_data():
    print("步驟 1/3: 開始從 API 獲取最新的食品營養資料...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(TFDA_API_URL, headers=headers)
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        print(f" -> 資料獲取成功！已讀取 {len(df)} 筆原始資料。")
    except Exception as e:
        print(f"處理 API 回應時發生錯誤: {e}")
        return

    print("步驟 2/3: 開始進行資料重塑 (Pivot) 與清洗...")
    
    df.columns = df.columns.str.strip()

    # --- 修改點：使用您提供的、最新的、正確的分析項名稱 ---
    nutrient_items = [
        '熱量', '粗蛋白', '粗脂肪', '飽和脂肪', 
        '反式脂肪', '總碳水化合物', '糖質總量', '鈉'
    ]
    df_filtered = df[df['分析項'].isin(nutrient_items)].copy()
    
    df_filtered.loc[:, '每100克含量'] = pd.to_numeric(df_filtered['每100克含量'], errors='coerce').fillna(0)

    df_pivoted = df_filtered.pivot_table(
        index=['整合編號', '樣品名稱'], 
        columns='分析項', 
        values='每100克含量'
    ).reset_index()

    # --- 修改點：使用最新的欄位名稱來建立對應 ---
    column_mapping = {
        '整合編號': 'tfda_id', '樣品名稱': 'food_name', '熱量': 'calories_kcal',
        '粗蛋白': 'protein_g', '粗脂肪': 'fat_g', '飽和脂肪': 'saturated_fat_g',
        '反式脂肪': 'trans_fat_g', '總碳水化合物': 'carbohydrate_g',
        '糖質總量': 'sugar_g', '鈉': 'sodium_mg'
    }
    df_pivoted.rename(columns=column_mapping, inplace=True)

    for db_col in column_mapping.values():
        if db_col not in df_pivoted.columns:
            df_pivoted[db_col] = 0
            
    print(" -> 資料重塑與清洗完成！")

    print(f"步驟 3/3: 開始將 {len(df_pivoted)} 筆資料同步到資料庫 '{DB_FILE}'...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    update_count = 0
    insert_count = 0
    for index, row in df_pivoted.iterrows():
        cursor.execute("SELECT id FROM ingredients WHERE tfda_id = ?", (str(row['tfda_id']),))
        result = cursor.fetchone()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        data_tuple_insert = (
            str(row['tfda_id']), row.get('food_name'), now, now,
            row.get('calories_kcal', 0), row.get('protein_g', 0), row.get('fat_g', 0),
            row.get('saturated_fat_g', 0), row.get('trans_fat_g', 0), row.get('carbohydrate_g', 0),
            row.get('sugar_g', 0), row.get('sodium_mg', 0), 0
        )
        data_tuple_update = (
            row.get('food_name'), row.get('calories_kcal', 0), row.get('protein_g', 0),
            row.get('fat_g', 0), row.get('saturated_fat_g', 0), row.get('trans_fat_g', 0),
            row.get('carbohydrate_g', 0), row.get('sugar_g', 0), row.get('sodium_mg', 0),
            now, str(row['tfda_id'])
        )

        if result:
            update_count += 1
            cursor.execute("UPDATE ingredients SET food_name=?, calories_kcal=?, protein_g=?, fat_g=?, saturated_fat_g=?, trans_fat_g=?, carbohydrate_g=?, sugar_g=?, sodium_mg=?, updated_at=? WHERE tfda_id = ?", data_tuple_update)
        else:
            insert_count += 1
            cursor.execute("INSERT INTO ingredients (tfda_id, food_name, source, created_at, updated_at, calories_kcal, protein_g, fat_g, saturated_fat_g, trans_fat_g, carbohydrate_g, sugar_g, sodium_mg, cost_per_unit) VALUES (?, ?, 'TFDA', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data_tuple_insert)
        
        if (index + 1) % 100 == 0:
            print(f" -> 已處理 {index + 1} / {len(df_pivoted)} 筆資料...")
    conn.commit()
    conn.close()
    print("\n匯入作業完成！")
    print(f"總共新增了 {insert_count} 筆新食材。")
    print(f"總共更新了 {update_count} 筆現有食材。")

if __name__ == '__main__':
    import_data()