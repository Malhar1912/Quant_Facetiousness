import numpy as np
import pandas as pd
import yfinance as yf
from hmmlearn import hmm
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
import warnings
import matplotlib.pyplot as plt

def load_data(ticker, start="2018-01-01", end="2025-12-31"):
    print(f"Downloading data for {ticker} from {start} to {end}...")
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    if "Open" not in df.columns:
        df["Open"] = df["Close"].shift(1)
        
    return df

def engineer_features(df):
    df = df.copy()
    close = df["Close"]
    volume = df["Volume"]

    log_ret = np.log(close / close.shift(1)).fillna(0)

    delta = close.diff()
    gain = (delta.clip(lower=0)).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))

    # REVERTED TO 252 to match the original 126% architecture
    amihud = (abs(log_ret) / (volume + 1e-8)).rolling(252).rank(pct=True) 

    high = df["High"]
    low = df["Low"]
    range_eff = abs(close - df["Open"]) / (high - low + 1e-8)

    vol = log_ret.rolling(20).std()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    ema10 = close.ewm(span=10).mean()
    momentum = close / close.shift(5) - 1

    feat_ret = log_ret * 100
    feat_vol = np.log(vol + 1e-8) * 100
    
    df_ml = pd.DataFrame({
        "open": df["Open"],
        "close": close,
        "log_ret": log_ret,
        "vol": vol,
        "feat_ret": feat_ret,
        "feat_vol": feat_vol,
        "amihud": amihud,
        "range_eff": range_eff,
        "momentum": momentum,
        "ma_dist": close / ma50 - 1,
        "rsi": rsi,
        "ma200": ma200,
        "ema10": ema10
    }, index=df.index)
    
    df_ml["target"] = (log_ret.shift(-1) > 0).astype(int)
    df_ml["target_cont"] = log_ret.shift(-1)
    
    return df_ml.dropna()

def label_hmm_states(model):
    vol_means = model.means_[:, 1]   
    order = np.argsort(vol_means)    
    return {
        "lowvol":  order[0],
        "midvol":  order[1],
        "highvol": order[2],
    }

def get_volatility_scaled_size(recent_vol: float, target_daily_vol: float = 0.01, max_size: float = 1.0, min_size: float = 0.20) -> float:
    if recent_vol <= 0:
        return min_size
    raw_size = target_daily_vol / recent_vol
    return float(np.clip(raw_size, min_size, max_size))

def evaluate_signal_quality(df_ml, window_train=252, window_test=63):
    results = []
    start = 0
    drop_cols = ["target", "target_cont", "open", "close", "log_ret", "vol", "ma200", "ema10"]
    existing_drop_cols = [c for c in drop_cols if c in df_ml.columns]

    while start + window_train + window_test <= len(df_ml):
        train = df_ml.iloc[start : start+window_train].copy()
        test  = df_ml.iloc[start+window_train : start+window_train+window_test].copy()
        
        X_tr = train.drop(columns=existing_drop_cols, errors='ignore')
        X_te = test.drop(columns=existing_drop_cols, errors='ignore')
        y_tr = train["target"]
        y_tr_continuous = train["target_cont"]
        y_te = test["target"]
        
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_te_s = scaler.transform(X_te)
        
        model = XGBClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3, 
            reg_alpha=0.1, reg_lambda=1.0, random_state=42
        )
        model.fit(X_tr_s, y_tr, sample_weight=np.abs(y_tr_continuous))
        
        preds = model.predict(X_te_s)
        acc = (preds == y_te).mean()
        results.append(acc)
        start += window_test
    
    return np.mean(results) if len(results) > 0 else 0.0

def run_walk_forward_backtest(df_ml, starting_capital=10000.0):
    window_train = 252
    window_test = 63
    
    print(f"\nStarting Walk-Forward Backtest (Train={window_train} days, Test={window_test} days)...")
    
    confidence_threshold = 0.54
    slippage_penalty = 0.001 
    min_hold = 5
    max_hold = 8
    
    capital = starting_capital
    equity_curve = []
    realized_trades = []
    
    start = 0
    position = 0
    pending_entry = False
    pending_exit = False
    entry_price = 0.0
    position_size = 0.0
    hold_days = 0
    downtrend_counter = 0
    consec_losses = 0
    circuit_breaker_timer = 0
    
    opens = df_ml["open"].values
    closes = df_ml["close"].values
    ma200_all = df_ml["ma200"].values
    ema10_all = df_ml["ema10"].values
    rsi_all = df_ml["rsi"].values

    for _ in range(window_train):
        equity_curve.append(capital)

    while start + window_train < len(df_ml):
        end_test = min(start + window_train + window_test, len(df_ml))
        current_test_len = end_test - (start + window_train)
        
        train = df_ml.iloc[start : start+window_train].copy()
        test = df_ml.iloc[start+window_train : end_test].copy()

        hmm_features = ["feat_ret", "feat_vol"]
        X_hmm_train = train[hmm_features].values
        X_hmm_test = test[hmm_features].values
        
        scaler_hmm = StandardScaler()
        X_hmm_train_scaled = scaler_hmm.fit_transform(X_hmm_train)
        X_hmm_test_scaled = scaler_hmm.transform(X_hmm_test)

        model_hmm = hmm.GaussianHMM(n_components=3, n_iter=1000, random_state=42)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model_hmm.fit(X_hmm_train_scaled)
        
        # PROPERLY APPENDING STATE TO BOTH TRAIN AND TEST
        train["state"] = model_hmm.predict(X_hmm_train_scaled)
        test["state"] = model_hmm.predict(X_hmm_test_scaled)

        state_map = label_hmm_states(model_hmm)
        high_vol_state = state_map["highvol"]
        low_vol_state  = state_map["lowvol"]

        # EXCLUDING STATE FROM DROP COLS
        drop_cols = ["target", "target_cont", "open", "close", "log_ret", "vol", "ma200", "ema10"]
        train_ml = train.iloc[:-1] 
        
        X_train_raw = train_ml.drop(columns=drop_cols, errors='ignore')
        y_train = train_ml["target"]
        y_train_continuous = train_ml["target_cont"]
        X_test_raw = test.drop(columns=drop_cols, errors='ignore')

        scaler_xgb = StandardScaler()
        X_train_scaled = scaler_xgb.fit_transform(X_train_raw)
        X_test_scaled = scaler_xgb.transform(X_test_raw)

        base_model = XGBClassifier(
            n_estimators=150, max_depth=3, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
            reg_alpha=0.1, reg_lambda=1.0,
            early_stopping_rounds=15, eval_metric="logloss",
            random_state=42
        )
        
        X_fit, X_cal, y_fit, y_cal, y_fit_cont, _ = train_test_split(X_train_scaled, y_train, y_train_continuous, test_size=0.2, shuffle=False)
        base_model.fit(X_fit, y_fit, sample_weight=np.abs(y_fit_cont), eval_set=[(X_cal, y_cal)], verbose=False)
        
        model_ml = CalibratedClassifierCV(base_model, method="isotonic", cv="prefit") if len(X_cal) >= 60 else base_model
        proba = model_ml.predict_proba(X_test_scaled)
            
        for i in range(current_test_len):
            idx = start + window_train + i
            current_date = df_ml.index[idx]
            
            today_open = opens[idx]
            today_close = closes[idx]
            
            if circuit_breaker_timer > 0:
                circuit_breaker_timer -= 1
                
            if pending_exit:
                exit_price = today_open * (1 - slippage_penalty)
                trade_ret = (exit_price / entry_price - 1) * position_size
                capital *= (1 + trade_ret)
                realized_trades.append({
                    "ret": trade_ret, "entry_day": df_ml.index[idx - hold_days],
                    "exit_day": current_date, "entry_price": entry_price, "exit_price": exit_price
                })
                position = 0
                pending_exit = False
                
                if trade_ret < 0:
                    consec_losses += 1
                    if consec_losses >= 3:
                        circuit_breaker_timer = 10
                        consec_losses = 0
                else:
                    consec_losses = 0
                
            elif pending_entry:
                entry_price = today_open * (1 + slippage_penalty)
                position = 1
                hold_days = 0
                pending_entry = False

            if position == 1:
                hold_days += 1
                paper_ret = (today_close / entry_price - 1) * position_size
                equity = capital * (1 + paper_ret)
            else:    
                equity = capital
            
            equity_curve.append(equity)
            
            ma200_slope = (ma200_all[idx] - ma200_all[idx-20]) / (ma200_all[idx-20] + 1e-8)
            uptrend = ma200_slope > -0.001
            downtrend_counter = downtrend_counter + 1 if not uptrend else 0

            current_state = test["state"].iloc[i]
            current_rsi = rsi_all[idx]
            
            if position == 0 and not pending_entry:
                prob_up = proba[i][1]

                mean_reversion_allowance = (not uptrend) and (current_rsi < 35) and (current_state != high_vol_state)
                valid_trend = uptrend or mean_reversion_allowance

                if circuit_breaker_timer == 0 and downtrend_counter <= 15 and prob_up > confidence_threshold and valid_trend and (15 < current_rsi < 80):
                    pending_entry = True

                    vol_window = df_ml["vol"].iloc[:idx + 1].tail(20)
                    recent_vol = vol_window.mean() if len(vol_window) > 0 else 0.015
                    base_size = get_volatility_scaled_size(recent_vol)

                    if current_state == high_vol_state:
                        position_size = base_size * 0.40   
                    elif current_state == low_vol_state:
                        position_size = base_size * 1.0
                    else:
                        position_size = base_size * 0.7

            elif position == 1 and not pending_exit:
                current_ema10 = ema10_all[idx]
                current_return = (today_close / entry_price) - 1

                if current_state == high_vol_state:
                    current_stop = -0.02
                elif current_state == low_vol_state:
                    current_stop = -0.04
                else:
                    current_stop = -0.03
                    
                hard_stop_triggered = current_return <= current_stop
                current_min_hold = 2 if current_state == high_vol_state else min_hold
                trend_broken = (today_close < current_ema10 and hold_days >= current_min_hold)
                
                strong_winner = (current_return > 0.015 and hold_days >= min_hold)
                effective_max_hold = max_hold + 2 if strong_winner else max_hold
                time_stop_exit = (hold_days >= effective_max_hold and current_return <= 0.0)

                if hard_stop_triggered or trend_broken or time_stop_exit:
                    pending_exit = True

        start += window_test

    equity_series = pd.Series(equity_curve[:len(df_ml)], index=df_ml.index)
    return equity_series, realized_trades

def calculate_metrics(equity_curve, realized_trades=None):
    returns = equity_curve.pct_change().fillna(0.0)
    
    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    rf_daily = 0.05 / 365 
    excess = returns - rf_daily
    sharpe = (np.mean(excess) / np.std(excess)) * np.sqrt(365) if np.std(excess) > 0 else 0.0
    
    sortino_downs = excess[excess < 0]
    sortino = (np.mean(excess) / np.std(sortino_downs)) * np.sqrt(365) if len(sortino_downs) > 0 else 0.0

    days = len(equity_curve)
    years = days / 365
    cagr = ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0
    volatility = np.std(returns) * np.sqrt(365) * 100

    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    max_dd = np.min(drawdown) * 100
    calmar = (cagr / abs(max_dd)) if max_dd != 0 else 0

    if realized_trades is not None:
        trade_opts = np.array([t["ret"] for t in realized_trades]) if len(realized_trades) > 0 else np.array([])
        total_trades = len(trade_opts)
        wins = trade_opts[trade_opts > 0]
        losses = trade_opts[trade_opts < 0]
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean(wins) * 100 if len(wins) > 0 else 0
        avg_loss = np.mean(losses) * 100 if len(losses) > 0 else 0
        profit_factor = abs(np.sum(wins) / np.sum(losses)) if len(losses) > 0 else 0
        expectancy = (win_rate/100 * avg_win + (1 - win_rate/100) * avg_loss)
    else:
        total_trades, win_rate, avg_win, avg_loss, profit_factor, expectancy = 0, 0, 0, 0, 0, 0

    return {
        "total_return": total_return, "cagr": cagr, "volatility": volatility,
        "sharpe": sharpe, "sortino": sortino, "max_dd": max_dd, "calmar": calmar,
        "total_trades": total_trades, "win_rate": win_rate, "avg_win": avg_win,
        "avg_loss": avg_loss, "profit_factor": profit_factor, "expectancy": expectancy
    }

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=FutureWarning) 
    
    ticker = "BTC-USD"
    INITIAL_CAPITAL = 10000.0
    
    print(f"\n{'='*80}\nPROCESSING TICKER: {ticker}\n{'='*80}")
    
    df_raw = load_data(ticker, start="2018-01-01", end="2025-12-31")
    df_ml = engineer_features(df_raw)
    
    acc = evaluate_signal_quality(df_ml)
    equity_series, trades = run_walk_forward_backtest(df_ml, starting_capital=INITIAL_CAPITAL)
    
    metrics = calculate_metrics(equity_series, trades)
    
    print(f"\nWALK-FORWARD FULL SET METRICS: {ticker}")
    print("-" * 40)
    print(f"XGB Test Accuracy:   {acc:.1%}")
    print(f"Total Return:        {metrics['total_return']:.2f}%")
    print(f"CAGR:                {metrics['cagr']:.2f}%")
    print(f"Sharpe Ratio:        {metrics['sharpe']:.2f}")
    print(f"Max Drawdown:        {metrics['max_dd']:.2f}%")
    print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
    print(f"Win Rate:            {metrics['win_rate']:.1f}% ({metrics['total_trades']} trades)")
    print(f"Trade Expectancy:    {metrics['expectancy']:.2f}%")
    print("="*80)

    active_equity_series = equity_series.iloc[252:]
    
    plt.figure(figsize=(12, 6))
    plt.plot(active_equity_series.index, active_equity_series.values, label=f'{ticker} Model Equity', color='blue', linewidth=2)
    plt.axhline(INITIAL_CAPITAL, color='red', linestyle='--', label='Initial Capital ($10,000)', alpha=0.7)
    
    plt.title(f'{ticker} Total Capital - Periodic Walk-Forward Backtest (2019-2025)', fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Capital (USD)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    plt.show()