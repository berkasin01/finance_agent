import pandas as pd
import yfinance as yf
import time

# 1) Load your cleaned DataFrame just to get the tickers
df = pd.read_csv("SHORT_WITH_YAHOO_MERGED.csv", parse_dates=["QuarterEnd"])
tickers = df["Ticker"].unique().tolist()

records = []
batch_size = 25
sleep_secs = 15
total = len(tickers)
num_batches = (total + batch_size - 1) // batch_size

for batch_i in range(num_batches):
    start = batch_i * batch_size
    end = min(start + batch_size, total)
    batch = tickers[start:end]
    print(f"\n=== Batch {batch_i+1}/{num_batches} — tickers {start+1} to {end} of {total} ===")
    for idx, t in enumerate(batch, start=start+1):
        print(f"[{idx}/{total}] Fetching {t}...", end="", flush=True)
        try:
            info = yf.Ticker(t).info
            records.append({
                "Ticker":          t,
                "Exchange":        info.get("exchange"),
                "Country":         info.get("country"),
            })
            print(" OK")
        except Exception:
            records.append({
                "Ticker":          t,
                "Exchange":        None,
                "Country":         None,
                        })
            print(" FAILED")
    if batch_i < num_batches - 1:
        print(f"Sleeping {sleep_secs}s before next batch…")
        time.sleep(sleep_secs)

# 4) Build the metadata DataFrame and export it
meta = pd.DataFrame(records)
meta.to_csv("more_company_info_to_add.csv", index=False)
print("\n Exported ticker metadata (with marketCap, P/B, EV) to tickers_exchange_country.csv")