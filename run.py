# --- 請將 run.py 的內容完整替換成以下程式碼 ---

print("檢查點 1: 開始執行 run.py")

try:
    from app import create_app
    print("檢查點 2: 成功從 app 模組匯入 create_app")

    app = create_app()
    print("檢查點 3: 成功呼叫 create_app() 並建立 app 物件")

    # 這是最關鍵的檢查點
    if __name__ == '__main__':
        print("檢查點 4: 成功進入 __name__ == '__main__' 判斷式，準備啟動伺服器...")
        app.run(debug=True)
    else:
        # 如果程式正常執行，這一段不應該被印出來
        print("警告: 未進入 __name__ == '__main__' 判斷式。")

except Exception as e:
    # 如果中間有任何我們沒預料到的錯誤，這個區塊會捕捉到並印出來
    print(f"\n！！！！發生了預期外的錯誤！！！！\n")
    print(f"錯誤類型: {type(e).__name__}")
    print(f"錯誤訊息: {e}")
    import traceback
    traceback.print_exc()