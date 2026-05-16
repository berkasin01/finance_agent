import pandas as pd
import yfinance as yf
from datetime import date

def get_prices_volume(tickers, start="2017-01-01", end=None, interval="1d", path="prices_volume_2017_today.csv"):
    end = end or date.today().isoformat()
    pieces = []
    for t in tickers:
        df = yf.download(t, start=start, end=end, interval=interval, progress=False, auto_adjust=False, threads=True)
        if df.empty:
            continue
        close_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        c = df[close_col].copy()
        if isinstance(c, pd.DataFrame):
            c = c.iloc[:, 0]
        if t == "^TNX" and c.dropna().median() > 20:
            c = c / 10.0
        c.name = f"{t}_Close"

        if "Volume" in df.columns:
            v = df["Volume"].copy()
            if isinstance(v, pd.DataFrame):
                v = v.iloc[:, 0]
            v.name = f"{t}_Volume"
        else:
            v = pd.Series(index=df.index, dtype="float64", name=f"{t}_Volume")

        pieces.append(pd.concat([c, v], axis=1))

    out = pd.concat(pieces, axis=1).sort_index()
    if getattr(out.index, "tz", None) is not None:
        out.index = out.index.tz_localize(None)

    out.drop(columns=["^VIX_Volume", "^TNX_Volume", "^NYICDX_Volume"], inplace=True)
    out.to_csv(path, float_format="%.6f")
    return out

tickers = ["GC=F", "^VIX", "TN=F", "^TNX", "^NYICDX"]
df = get_prices_volume(tickers, path="../additional_info_to_add/prices_volume_2017_today.csv")
print(df.tail())
print("Saved to prices_volume_2017_today.csv")
