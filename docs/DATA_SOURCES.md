# Data Sources

| Data | Source / status | Purpose |
|---|---|---|
| M5-derived multi-product sales | Public M5 Forecasting dataset derivative supplied with project | Demand forecasting, anomaly detection |
| Multi-product recommendation artifact | Derived from supplied M5/inventory data | Initial risk/reorder baseline and fallback |
| Inventory snapshot | Project operational snapshot | Current/incoming stock, lead time |
| Factory capacity | Supplied RetailEdge PostgreSQL dump | Prototype capacity check |
| Raw materials | Supplied RetailEdge PostgreSQL dump | Prototype material check |
| Production/dispatch/delivery | Supplied RetailEdge PostgreSQL dump | Supply-chain workflow demo |
| Customer preferences/feedback | Supplied RetailEdge PostgreSQL dump | Personalization/feedback context |
| Weather, festival, promotions, trends | Bundled project context datasets | Context analysis; not treated as live values |

Operational factory and supply-chain records are explicitly prototype/demo data. The application does not claim them to be live factory ERP data.
