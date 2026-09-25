import requests

BASE = "http://127.0.0.1:8003"

def check(method, path, **kwargs):
    r = requests.request(method, BASE + path, timeout=90, **kwargs)
    r.raise_for_status()
    return r.json()

assert check("GET", "/health")["status"] == "healthy"
assert check("POST", "/api/login", json={"username":"demo","password":"1234","role":"retailer"})["status"] == "success"
r = check("GET", "/api/ai-insights?product=FOODS_3_090&store=CA_1")
assert r["model"] in ["XGBoost Regressor", "MVP precomputed forecast artifact"]
assert len(r["forecast"]) == 7
assert "recommended_order" in r["inventory"]
assert check("GET", "/api/inventory-risk")["count"] if "count" in check("GET", "/api/inventory-risk") else True
order = check("POST", "/api/purchase-orders", json={"product":"FOODS_3_090","store":"CA_1","quantity":3})["order"]
for status in ["ACCEPTED", "IN PRODUCTION", "READY", "DISPATCHED", "DELIVERED"]:
    out = check("PUT", f"/api/purchase-orders/{order['order_id']}/status", json={"status":status})
    assert out["order"]["status"] == status
sent = check("POST", "/api/customer/feedback", json={"product":"FOODS_3_090","feedback":"Excellent and fast","rating":5})
assert sent["sentiment"] == "POSITIVE"
assert check("GET", "/api/admin/overview")["status"] == "success"
print("ALL SMOKE TESTS PASSED")
