import argparse
import sys
import yfinance as yf
import pandas as pd

# --------- CLI / 輸入模組 ---------
# 負責解析命令列參數，若未提供 stock_id 則互動式提示輸入
def parse_args():
    parser = argparse.ArgumentParser(description="Buffett 選股法自動化篩選工具")
    parser.add_argument("stock_id", nargs="?", help="台股代碼 (e.g. 2330)")  # 可選參數
    parser.add_argument("--years_eps", type=int, default=5, help="要抓取的 EPS 年數，預設 5 年")
    parser.add_argument("--quarters_rev", type=int, default=4, help="要抓取的每股營收季數，預設 4 季")
    args = parser.parse_args()
    # 若未於參數中提供 stock_id，則以 input() 互動提示
    if not args.stock_id:
        args.stock_id = input("請輸入股票代碼: ").strip()
    return args

# --------- 資料擷取模組 ---------
# 從 yfinance 取得股票基本資訊與財報，再計算所需指標
def fetch_financials(stock_id, years_eps, quarters_rev):
    ticker = yf.Ticker(f"{stock_id}.TW")  # 台股需加 .TW 後綴
    info = ticker.info or {}

    # 1. 現價 & 每股淨值
    price = info.get("regularMarketPrice")  # 當前市價
    bvps = info.get("bookValue")           # 每股淨值
    if price is None or bvps is None:
        raise ValueError("無法取得當前股價或每股淨值")

    # 2. 年度 EPS
    eps_list = []
    shares = info.get('sharesOutstanding')  # 在外流通股數
    # 先嘗試從 incomeStatementHistory 取 netIncome
    for rec in info.get('incomeStatementHistory', {}).get('incomeStatementHistory', [])[:years_eps]:
        ni = rec.get('netIncome', {}).get('raw')
        if ni and shares:
            eps_list.append(ni / shares)
    # 若筆數不足，fallback 使用 trailingEps
    if len(eps_list) < years_eps:
        trailing = info.get('trailingEps')
        if trailing is None:
            raise ValueError("無法取得年度 EPS")
        eps_list = [trailing] * years_eps

    # 3. 季度營收
    qf = ticker.quarterly_financials
    # 取 Total Revenue 前 quarters_rev 筆
    rev = qf.loc['Total Revenue'].tolist()[:quarters_rev] if 'Total Revenue' in qf.index else []
    if len(rev) < quarters_rev:
        raise ValueError("季度營收資料不足")

    # 4. 季度 ROE
    roe = []
    # 優先用每季淨利 / 總股東權益
    if 'Net Income' in qf.index and info.get('totalStockholderEquity'):
        equity = info['totalStockholderEquity']
        raw_ni = qf.loc['Net Income'].tolist()[:quarters_rev]
        if len(raw_ni) == quarters_rev:
            roe = [(ni / equity) * 100 for ni in raw_ni]
    # 若不足則 fallback
    if len(roe) < quarters_rev:
        fallback_roe = info.get('trailingReturnOnEquity') or info.get('returnOnEquity')
        if fallback_roe is None:
            raise ValueError("無法取得季度 ROE 資料")
        roe = [fallback_roe] * quarters_rev

    # 5. 年度毛利率
    fin = ticker.financials
    if 'Gross Profit' in fin.index and 'Total Revenue' in fin.index:
        gp = fin.loc['Gross Profit'].tolist()[:years_eps]
        tr = fin.loc['Total Revenue'].tolist()[:years_eps]
        if len(gp) < years_eps or len(tr) < years_eps:
            raise ValueError("年度毛利率資料不足")
        gm = [(g / t) * 100 for g, t in zip(gp, tr)]
    else:
        raise ValueError("無法取得年度毛利率資料")

    # 回傳字典，包含所有指標列表與價格資訊
    return {
        'eps_5y': eps_list,
        'rev_4q': rev,
        'roe_4q': roe,
        'gm_5y': gm,
        'price': price,
        'bvps': bvps,
    }

# --------- 分析 & 篩選模組 ---------
# 計算 P/B Ratio，並執行 Buffett 條件篩選

def calculate_indicators(data):
    data['pb_ratio'] = data['price'] / data['bvps']  # 計算 P/B
    return data


def apply_buffett_criteria(data):
    return {
        '近5年 EPS > 1':      all(x > 1 for x in data['eps_5y']),
        '近4季每股營收 > 1.5': all(x > 1.5 for x in data['rev_4q']),
        '股價淨值比 < 1.5':    data['pb_ratio'] < 1.5,
        '近4季 ROE > 5%':     all(x > 5 for x in data['roe_4q']),
        '近5年毛利率 > 10%':   all(x > 10 for x in data['gm_5y']),
    }

# --------- 輸出模組 ---------
# 顯示各項條件是否通過，並以符號標示

def display_results(stock_id, criteria_results):
    print(f"\n=== {stock_id} 篩選結果 ===")
    for desc, ok in criteria_results.items():
        print(f"{desc}: {'✅ 通過' if ok else '❌ 未通過'}")
    # 最終建議
    print(f"\n📈 可投資" if all(criteria_results.values()) else f"\n📉 不建議投資")

# --------- 主程式 ---------
def main():
    # 解析參數
    args = parse_args()
    try:
        # 抓取並處理資料
        data = fetch_financials(args.stock_id, args.years_eps, args.quarters_rev)
    except Exception as e:
        # 錯誤處理
        print("資料擷取或處理失敗：", e)
        sys.exit(1)
    # 計算及篩選
    data = calculate_indicators(data)
    crit = apply_buffett_criteria(data)
    # 輸出結果
    display_results(args.stock_id, crit)

if __name__ == "__main__":
    main()