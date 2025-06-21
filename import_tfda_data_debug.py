# --- 100% 完整程式碼 ---

import requests
import pandas as pd

API_URL = "https://data.fda.gov.tw/opendata/exportDataList.do?method=openData&InfoId=20"

def find_analysis_items():
    print("正在從 API 獲取資料...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        df = pd.DataFrame(response.json())
        print(" -> 資料獲取成功！")
        
        # 清理欄位名稱中可能存在的前後空白
        df.columns = df.columns.str.strip()

        if '分析項' not in df.columns:
            print("錯誤：找不到 '分析項' 欄位。")
            print(f"偵測到的所有欄位為: {list(df.columns)}")
            return

        # 取得 '分析項' 欄位中所有不重複的值
        unique_items = df['分析項'].unique()

        print("\n偵測到的所有獨特的『分析項』名稱如下：")
        print("========================================")
        # 為了方便閱讀，我們一個一個印出來
        for item in sorted(list(unique_items)):
            print(item)
        print("========================================")

    except Exception as e:
        print(f"處理 API 回應時發生錯誤: {e}")

if __name__ == '__main__':
    find_analysis_items()