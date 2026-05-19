import numpy as np

def calculate_trend(prices: list[float]) -> float:
    if len(prices) < 3:
        return 0.0
    x = np.arange(len(prices))
    y = np.array(prices)
    slope = np.polyfit(x, y, 1)[0]  # regressão linear
    return float(slope)

def calculate_volatility(prices: list[float]) -> float:
    if len(prices) < 3:
        return 0.0
    returns = np.diff(prices) / prices[:-1]
    return float(np.std(returns))