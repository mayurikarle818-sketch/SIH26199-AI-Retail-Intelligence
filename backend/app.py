from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import os, pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

def data_path(name): return os.path.join(DATA_DIR, name)

def read_csv(name):
    p=data_path(name)
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

from backend.database import SessionLocal, CustomerFeedback, PurchaseOrder, ProductionOrder, DispatchRecord, engine, IS_POSTGRES
from backend.ai_engine import forecast, inventory_intelligence, recommendation, anomaly_detection, customer_recommendations, sentiment, sales
from backend.order_engine import create_order, list_orders, update_status, production_for, dispatch_for, serialize_order, serialize_production, serialize_dispatch, STATUS_FLOW

app = FastAPI(title="SIH26179 AI Retail & Supply Chain Intelligence Platform", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

DB_TABLES={
 "sales":"team_m5_multi_product_sales","predictions":"team_multi_product_predictions","recommendations":"team_multi_product_recommendations","inventory":"team_inventory_multi_product","calendar":"team_calendar","factory_capacity":"prati_factory_capacity_data","raw_material":"prati_raw_material_data","production_orders":"prati_production_order_data","production_status":"prati_production_status_data","dispatch":"prati_dispatch_data","delivery":"prati_delivery_status_data","customer_feedback":"prati_customer_feedback_data","customer_preferences":"prati_customer_preference_data","products":"prati_product_master_data"
}

def db_df(key):
    if not IS_POSTGRES: return pd.DataFrame()
    try: return pd.read_sql_query(f'SELECT * FROM public."{DB_TABLES[key]}"', engine)
    except Exception: return pd.DataFrame()

def data_df(key, csv_name):
    df=db_df(key)
    return df if not df.empty else read_csv(csv_name)

@app.get("/", include_in_schema=False)
def home(): return RedirectResponse(url="/frontend/index.html")
@app.get("/health")
def health(): return {"status":"healthy","service":"SIH26179","version":"3.0.0"}

class LoginRequest(BaseModel): username:str; password:str; role:str
DEMO_USERS={"retailer":"retailer123","factory":"factory123","customer":"customer123","admin":"admin123"}
@app.post("/api/login")
def login(data:LoginRequest):
    role=data.role.strip().lower()
    username=data.username.strip()
    password=data.password.strip()
    if role not in DEMO_USERS or not ((username == "demo" and password == "1234") or password == DEMO_USERS[role]): raise HTTPException(401,"Invalid demo credentials")
    return {"status":"success","role":role,"username":username or role,"demo":True}

@app.get("/api/recommendation")
def get_recommendation(product:str|None=None, store:str="CA_1"):
    try: return {"status":"success", **recommendation(product,store)}
    except Exception as e: raise HTTPException(404,str(e))

@app.get("/api/inventory-risk")
def inventory_risk():
    rows=inventory_intelligence(); counts={k:sum(x["risk"]==k for x in rows) for k in ["CRITICAL","HIGH","MEDIUM","LOW"]}
    return {"status":"success","summary":counts,"inventory":rows,"source":"M5-derived sales + operational inventory snapshot"}

@app.get("/api/alerts")
def alerts():
    rows=inventory_intelligence(); alerts=[]
    for r in rows:
        if r["risk"] in ["CRITICAL","HIGH"]:
            alerts.append({"type":r["risk"],"title":f"{r['risk'].title()} Inventory Risk","product":r["product"],"message":f"Stock cover {r['stock_cover_days']} days; reorder {r['recommended_order']} units.","action":"PLACE PURCHASE ORDER"})
    orders=list_orders()
    for o in orders:
        if o.status not in ["DELIVERED"]:
            alerts.append({"type":"ORDER","title":"Pending Supply Chain Order","product":o.product,"message":f"{o.order_id} is {o.status}.","action":o.status})
    return {"status":"success","alert_count":len(alerts),"alerts":alerts}

class Feedback(BaseModel): product:str; store:str="CA_1"; feedback:str
@app.post("/api/feedback")
def submit_feedback(data:Feedback):
    value=data.feedback.lower().strip()
    if value not in ["helpful","not_helpful"]: raise HTTPException(400,"Feedback must be helpful or not_helpful")
    p=data_path("feedback.csv"); df=read_csv("feedback.csv")
    row=pd.DataFrame([[datetime.now().isoformat(),data.product,data.store,value]],columns=["timestamp","product","store","feedback"])
    pd.concat([df,row],ignore_index=True).to_csv(p,index=False)
    return {"status":"success","message":"Recommendation feedback saved","feedback":value}

class AssistantRequest(BaseModel): question:str
@app.post("/api/assistant")
def assistant(data:AssistantRequest):
    q=data.question.lower(); rows=inventory_intelligence();
    if "high risk" in q or "critical" in q: selected=[r for r in rows if r["risk"] in ["HIGH","CRITICAL"]]
    elif "reorder" in q or "order" in q: selected=sorted(rows,key=lambda x:x["recommended_order"],reverse=True)[:3]
    elif "low stock" in q or "stock" in q: selected=sorted(rows,key=lambda x:x["available_stock"])[:3]
    elif "forecast" in q or "demand" in q: selected=sorted(rows,key=lambda x:x["predicted_daily_demand"],reverse=True)[:3]
    else: selected=sorted(rows,key=lambda x:x["recommended_order"],reverse=True)[:3]
    if not selected: answer="No matching project data is available."
    else: answer="; ".join([f"{r['product']}: risk {r['risk']}, demand {r['predicted_daily_demand']}/day, stock {r['available_stock']}, reorder {r['recommended_order']}" for r in selected])
    return {"status":"success","question":data.question,"answer":answer,"data_used":"live backend inventory intelligence"}

@app.get("/api/products")
def products():
    # Product listing includes the same live AI fields used by the dashboard.
    result = inventory_intelligence()
    return {"status":"success","count":len(result),"products":result,"source":"M5-derived sales + operational inventory snapshot"}

@app.get("/api/context")
def context_endpoint(product:str="FOODS_3_090", store:str="CA_1"):
    from backend.ai_engine import context_for
    return {"status":"success", "product":product, "store":store, **context_for(product, store)}

@app.get("/api/sales")
def sales_endpoint():
    df=read_csv("m5_multi_product_sales.csv"); df["date"]=pd.to_datetime(df.date); df=df.sort_values("date").tail(60)
    return {"status":"success","count":len(df),"sales":[{"date":r.date.strftime('%Y-%m-%d'),"product":r.item_id,"store":r.store_id,"units_sold":int(r.sales)} for r in df.itertuples()],"source":"M5 Forecasting dataset derivative"}

@app.get("/api/multi-products")
def multi_products():
    rows = inventory_intelligence()
    return {
        "status": "success",
        "count": len(rows),
        "products": rows,
        "source": "Live XGBoost demand forecast + inventory intelligence"
    }

@app.get("/api/forecast/{product_id}")
def forecast_endpoint(product_id:str, store_id:str="CA_1"):
    try: return {"status":"success","product":product_id,"store":store_id,**forecast(product_id,store_id,7)}
    except Exception as e: raise HTTPException(404,str(e))

@app.get("/api/anomaly/{product_id}")
def anomaly(product_id:str, store_id:str="CA_1"):
    try: return {"status":"success",**anomaly_detection(product_id,store_id)}
    except Exception as e: raise HTTPException(404,str(e))

@app.get("/api/ai-insights")
def ai_insights(product:str="FOODS_3_090", store:str="CA_1"):
    f=forecast(product,store,7); r=recommendation(product,store); a=anomaly_detection(product,store)
    return {"status":"success","pipeline":["M5 sales data","preprocessing + lag features","XGBoost model","7-day prediction","inventory risk","explainable reorder recommendation","purchase order"],"model":f["model"],"features":f["features"],"mae":f.get("mae"),"forecast":f["forecast"],"feature_importance":f.get("feature_importance",[]),"inventory":r,"anomaly":a}

class OrderRequest(BaseModel): product:str; store:str="CA_1"; quantity:int=Field(gt=0); retailer:str="Retail Store 1"; factory:str="Factory A"; priority:str="HIGH"
@app.post("/api/purchase-orders")
def place_order(data:OrderRequest): return {"status":"success","order":serialize_order(create_order(**data.model_dump()))}
@app.get("/api/purchase-orders")
def get_orders(): return {"status":"success","orders":[serialize_order(o) for o in list_orders()]}
class StatusRequest(BaseModel): status:str
@app.put("/api/purchase-orders/{order_id}/status")
def set_status(order_id:str,data:StatusRequest):
    if data.status not in STATUS_FLOW: raise HTTPException(400,"Invalid status")
    o=update_status(order_id,data.status)
    if not o: raise HTTPException(404,"Order not found")
    return {"status":"success","order":serialize_order(o),"production":serialize_production(production_for(order_id)),"dispatch":serialize_dispatch(dispatch_for(order_id))}

@app.get("/api/factory/orders")
def factory_orders(): return get_orders()
@app.get("/api/factory/production/{order_id}")
def factory_production(order_id:str):
    p=production_for(order_id)
    if not p:
        orders=[o for o in list_orders() if o.order_id==order_id]
        if not orders: raise HTTPException(404,"Order not found")
        o=orders[0]
        from backend.order_engine import build_production_plan
        f,req,cap,raw,rec=build_production_plan(o)
        return {"status":"success","production":{"order_id":o.order_id,"product":o.product,"order_quantity":o.quantity,"finished_stock":f,"production_required":req,"capacity":cap,"raw_material_status":raw,"recommendation":rec,"status":o.status}}
    return {"status":"success","production":serialize_production(p)}

@app.get("/api/factory/capacity")
def factory_capacity():
    df=read_csv("factory_capacity.csv"); return {"status":"success","count":len(df),"data":df.fillna("").to_dict(orient="records"),"source":"Supplied PostgreSQL operational dataset"}
@app.get("/api/factory/raw-materials")
def factory_raw_materials():
    df=read_csv("raw_material.csv"); return {"status":"success","count":len(df),"data":df.fillna("").to_dict(orient="records"),"source":"Supplied PostgreSQL operational dataset"}
@app.get("/api/factory/production-data")
def factory_production_data():
    return {"status":"success","orders":read_csv("production_orders.csv").fillna("").to_dict(orient="records"),"production_status":read_csv("production_status.csv").fillna("").to_dict(orient="records"),"source":"Supplied PostgreSQL operational dataset"}
@app.get("/api/factory/dispatch-data")
def factory_dispatch_data():
    return {"status":"success","dispatch":read_csv("dispatch.csv").fillna("").to_dict(orient="records"),"delivery":read_csv("delivery.csv").fillna("").to_dict(orient="records"),"source":"Supplied PostgreSQL operational dataset"}

@app.get("/api/customer/products")
def customer_products():
    rows=inventory_intelligence()
    return {"status":"success","products":[{
        "product":r["product"],"store":r["store"],"available":r["available_stock"]>0,
        "available_stock":r["available_stock"],"predicted_daily_demand":r["predicted_daily_demand"],
        "risk":r["risk"],"stockout_days":r["stockout_days"]
    } for r in rows]}

@app.get("/api/customer/purchase-history")
def customer_purchase_history():
    orders=list_orders()
    return {"status":"success","orders":[serialize_order(o) for o in orders[:20]]}

@app.get("/api/customer/notifications")
def customer_notifications():
    rows=inventory_intelligence()
    notes=[]
    for r in rows:
        if r["available_stock"]<=0 or r["risk"] in ["CRITICAL","HIGH"]:
            notes.append({"product":r["product"],"type":"LOW_STOCK","message":f"Limited availability: {r['available_stock']} units available; estimated stock cover {r['stock_cover_days']:.1f} days."})
    return {"status":"success","notifications":notes[:10]}

class CustomerFeedbackRequest(BaseModel): product:str; feedback:str; rating:int|None=None
@app.post("/api/customer/feedback")
def customer_feedback(data:CustomerFeedbackRequest):
    s=sentiment(data.feedback)
    db=SessionLocal(); row=CustomerFeedback(product=data.product,feedback=data.feedback,rating=data.rating,sentiment=s["sentiment"]); db.add(row); db.commit(); db.close()
    return {"status":"success",**s,"message":"Customer feedback saved"}
@app.get("/api/customer/feedback-history")
def customer_feedback_history():
    db=SessionLocal(); rows=db.query(CustomerFeedback).order_by(CustomerFeedback.id.desc()).limit(30).all(); db.close()
    return {"status":"success","count":len(rows),"feedback":[{"product":r.product,"rating":r.rating,"feedback":r.feedback,"sentiment":r.sentiment,"created_at":r.created_at.isoformat() if r.created_at else None} for r in rows]}
@app.get("/api/customer/recommendations")
def customer_recs(customer_id:str="CUST_DEMO_001"): return {"status":"success","recommendations":customer_recommendations(customer_id)}

@app.get("/api/db-status")
def db_status():
    return {"status":"success","database":"PostgreSQL" if IS_POSTGRES else "SQLite MVP workflow + CSV analytics fallback","postgresql_connected":IS_POSTGRES,"workflow_tables":["purchase_orders","production_orders","dispatch_records","customer_feedback"]}

@app.get("/api/admin/overview")
def admin_overview():
    orders=list_orders(); inv=inventory_intelligence(); db=SessionLocal(); po=db.query(PurchaseOrder).count(); prod=db.query(ProductionOrder).count(); dispatch=db.query(DispatchRecord).count(); fb=db.query(CustomerFeedback).count(); db.close()
    return {"status":"success","products":len(inv),"critical_risk":sum(r["risk"]=="CRITICAL" for r in inv),"high_risk":sum(r["risk"]=="HIGH" for r in inv),"orders":po,"production_records":prod,"dispatch_records":dispatch,"feedback_records":fb,"database":"PostgreSQL" if IS_POSTGRES else "SQLite"}

@app.get("/api/production-plan/{order_id}")
def production_plan(order_id:str):
    o=next((x for x in list_orders() if x.order_id==order_id),None)
    if not o: raise HTTPException(404,"Order not found")
    from backend.order_engine import build_production_plan
    f,req,cap,raw,rec=build_production_plan(o)
    return {"status":"success","order_id":order_id,"finished_stock":f,"production_required":req,"capacity":cap,"raw_material_status":raw,"ai_recommendation":rec}
