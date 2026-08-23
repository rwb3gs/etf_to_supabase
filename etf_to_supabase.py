import requests
from supabase import create_client, Client

# ==========================================
# 1. 設定 Supabase 連線資訊
# ==========================================
SUPABASE_URL = "https://mmuyfyzbiuovjlvvodsp.supabase.co"
SUPABASE_KEY = "sb_publishable_jhv1343euvvQuFJ34eZczA_Kb6xvoGh"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 2. 證交所官方正式 OpenAPI 端點
# ==========================================
twse_url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "accept": "application/json"
}

try:
    response = requests.get(twse_url, headers=headers, timeout=15)
    
    # 檢查 HTTP 狀態碼是否為 200
    if response.status_code != 200:
        print(f"API 回傳異常，狀態碼: {response.status_code}")
        print(f"回傳內容: {response.text[:200]}") # 印出前200字輔助除錯
    else:
        raw_data = response.json()
        print(f"成功取得證交所資料，共 {len(raw_data)} 筆全市場行情。")

        # ==========================================
        # 3. 整理資料格式（對齊 Supabase 欄位）
        # ==========================================
        insert_data = []

        for item in raw_data:
            code = item.get("Code")
            name = item.get("Name")
            
            #STOCK_DAY_ALL 的欄位為 ClosingPrice (收盤價)
            raw_price = item.get("ClosingPrice") 

            # 過濾：只抓取 ETF (台股 ETF 證券代號通常為 00 開頭)
            if code and code.startswith("00"):
                # 處理數字中的逗號與無效字串
                try:
                    net_val = float(str(raw_price).replace(",", "").strip()) if raw_price else 0.0
                except ValueError:
                    net_val = 0.0

                #STOCK_DAY_ALL 屬於當日行情，可加上當天日期（格式 YYYY-MM-DD）
                from datetime import date
                today_str = date.today().isoformat()

                insert_data.append({
                    "code": code,
                    "name": name,
                    "net_value": net_val, # 存入收盤價格/淨值
                    "data_date": today_str
                })

        # ==========================================
        # 4. 批次寫入 Supabase
        # ==========================================
        if insert_data:
            result = supabase.table("etf_daily_nav").upsert(insert_data).execute()
            print(f"成功！已順利匯入 {len(insert_data)} 筆 ETF 資料至 Supabase。")
        else:
            print("沒有過濾出有效的 ETF 資料。")

except requests.exceptions.RequestException as e:
    print(f"請求失敗: {e}")
except Exception as e:
    print(f"程式執行時發生錯誤: {e}")