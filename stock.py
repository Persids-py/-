# 定義一個函式，用來取得使用者輸入的浮點數清單
def get_float_list(prompt, count):
    while True:
        try:
            # 提示使用者輸入數據（用逗號分隔）
            values = input(f"{prompt}（用逗號分隔，預期 {count} 筆）: ").split(",")
            # 移除空格並轉成 float
            values = [float(v.strip()) for v in values]
            # 如果筆數不對，拋出錯誤
            if len(values) != count:
                raise ValueError("筆數不符")
            return values
        except ValueError:
            print("輸入格式錯誤，請重新輸入。")

def main():
    # 輸入股票代碼
    stock_id = input("請輸入股票代碼: ")

    # 輸入五年 EPS
    eps_5y = get_float_list("輸入近5年 EPS", 5)

    # 輸入四季營收
    revenue_4q = get_float_list("輸入近4季每股營收", 4)

    # 輸入四季 ROE（股東權益報酬率）
    roe_4q = get_float_list("輸入近4季 ROE（%）", 4)

    # 輸入五年毛利率
    gross_margin_5y = get_float_list("輸入近5年毛利率（%）", 5)

    # 輸入目前股價與每股淨值
    try:
        price = float(input("輸入當前股價: "))
        book_value_per_share = float(input("輸入每股淨值: "))
    except ValueError:
        print("股價或淨值格式錯誤")
        return

    # 計算股價淨值比（P/B Ratio）
    pb_ratio = price / book_value_per_share

    # 檢查每個條件是否通過
    conditions = {
        "1. 近5年 EPS > 1": all(eps > 1 for eps in eps_5y),
        "2. 近4季每股營收 > 1.5元": all(r > 1.5 for r in revenue_4q),
        "3. 股價淨值比 < 1.5": pb_ratio < 1.5,
        "4. 近4季 ROE > 5%": all(r > 5 for r in roe_4q),
        "5. 近5年毛利率 > 10%": all(gm > 10 for gm in gross_margin_5y),
    }

    # 顯示結果
    print("\n=== 評估結果 ===")
    for desc, passed in conditions.items():
        print(f"{desc}: {'✅ 通過' if passed else '❌ 未通過'}")

    # 結論
    if all(conditions.values()):
        print(f"\n📈 根據華倫巴菲特選股法，股票 {stock_id} 適合投資。")
    else:
        print(f"\n📉 股票 {stock_id} 不符合巴菲特選股條件，不建議投資。")

# 主程式執行區
if __name__ == "__main__":
    main()
