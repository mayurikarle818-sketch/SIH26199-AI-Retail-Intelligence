# AI / ML Pipeline

1. M5-derived historical sales are loaded from `data/m5_multi_product_sales.csv`.
2. For a selected product/store, chronological lag and rolling features are created:
   - lag_1
   - lag_7
   - rolling_7
   - rolling_30
   - month
   - weekday
3. XGBoost Regressor is trained on the first 80% of the time series.
4. The final 20% is held out chronologically and MAE is calculated.
5. A recursive 7-day forecast is generated.
6. Forecast demand is combined with inventory, incoming stock, lead time and safety stock.
7. Inventory risk and stock-out days are calculated.
8. The reorder point is converted into a recommended order quantity.
9. The explanation exposes the main numerical factors and, for XGBoost, feature importance.
10. Isolation Forest checks recent sales for anomalies.
11. Customer feedback is scored with TextBlob polarity and labelled Positive/Neutral/Negative.

The UI does not display fabricated model metrics: MAE comes from the actual chronological hold-out used by the forecast service.
