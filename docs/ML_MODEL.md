# ML Model Plan

The forecasting pipeline uses time-based validation and compares baseline, festival/context feature sets. Metrics include MAE and RMSE, with WAPE/MAPE considered where appropriate. The current API exposes a 7-day forecast contract. Do not publish model accuracy until the final training run produces the metric.
