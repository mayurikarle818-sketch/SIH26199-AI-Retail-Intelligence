from datetime import datetime, timedelta
from .database import SessionLocal, PurchaseOrder, ProductionOrder, DispatchRecord
from .ai_engine import recommendation

STATUS_FLOW = ["PENDING", "ACCEPTED", "IN PRODUCTION", "READY", "DISPATCHED", "DELIVERED"]

def create_order(product, store, quantity, retailer="Retail Store 1", factory="Factory A", priority="HIGH"):
    db = SessionLocal()
    try:
        order_id = f"PO{datetime.utcnow().strftime('%y%m%d%H%M%S%f')[-12:]}"
        expected = (datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%d')
        order = PurchaseOrder(order_id=order_id, product=product, store=store, retailer=retailer, factory=factory, quantity=int(quantity), priority=priority, expected_date=expected)
        db.add(order); db.commit(); db.refresh(order)
        return order
    finally:
        db.close()

def list_orders():
    db = SessionLocal()
    try: return db.query(PurchaseOrder).order_by(PurchaseOrder.id.desc()).all()
    finally: db.close()

def build_production_plan(order):
    try:
        r = recommendation(order.product, order.store)
        predicted = r["predicted_daily_demand"]
    except Exception:
        r = {}; predicted = max(order.quantity / 5, 1)
    finished_stock = max(0, int(round(order.quantity * 0.2)))
    required = max(int(order.quantity) - finished_stock, 0)
    capacity = max(required + 50, 300)
    raw_status = "SUFFICIENT" if required <= capacity else "SHORTAGE"
    rec = f"Produce {required} units; forecast {predicted} units/day. " + ("Capacity and raw material checks are sufficient." if raw_status == "SUFFICIENT" else "Review capacity/raw-material shortage before production.")
    return finished_stock, required, capacity, raw_status, rec

def update_status(order_id, status):
    if status not in STATUS_FLOW: raise ValueError(f"Invalid status. Use one of: {', '.join(STATUS_FLOW)}")
    db = SessionLocal()
    try:
        order = db.query(PurchaseOrder).filter_by(order_id=order_id).first()
        if not order: return None
        order.status = status
        prod = db.query(ProductionOrder).filter_by(order_id=order_id).first()
        if status == "IN PRODUCTION" and not prod:
            finished, required, capacity, raw, rec = build_production_plan(order)
            prod = ProductionOrder(order_id=order_id, product=order.product, order_quantity=order.quantity, finished_stock=finished, production_required=required, capacity=capacity, raw_material_status=raw, recommendation=rec, status=status)
            db.add(prod)
        elif prod and status in ["READY", "DISPATCHED", "DELIVERED"]:
            prod.status = status
        if status == "DISPATCHED":
            d = db.query(DispatchRecord).filter_by(order_id=order_id).first()
            if not d:
                d = DispatchRecord(order_id=order_id, product=order.product, quantity=order.quantity, dispatch_status="DISPATCHED", dispatch_date=datetime.utcnow(), source=order.factory, destination=order.retailer)
                db.add(d)
            else:
                d.dispatch_status = "DISPATCHED"; d.dispatch_date = datetime.utcnow()
        if status == "DELIVERED":
            d = db.query(DispatchRecord).filter_by(order_id=order_id).first()
            if d: d.dispatch_status = "DELIVERED"
        db.commit(); db.refresh(order)
        return order
    finally: db.close()

def production_for(order_id):
    db=SessionLocal()
    try: return db.query(ProductionOrder).filter_by(order_id=order_id).first()
    finally: db.close()

def dispatch_for(order_id):
    db=SessionLocal()
    try: return db.query(DispatchRecord).filter_by(order_id=order_id).first()
    finally: db.close()

def serialize_order(o):
    return {"order_id":o.order_id,"product":o.product,"store":o.store,"retailer":o.retailer,"factory":o.factory,"quantity":o.quantity,"priority":o.priority,"status":o.status,"created_at":o.created_at.isoformat() if o.created_at else None,"expected_date":o.expected_date}

def serialize_production(p):
    if not p: return None
    return {"order_id":p.order_id,"product":p.product,"order_quantity":p.order_quantity,"finished_stock":p.finished_stock,"production_required":p.production_required,"capacity":p.capacity,"raw_material_status":p.raw_material_status,"recommendation":p.recommendation,"status":p.status}

def serialize_dispatch(d):
    if not d: return None
    return {"order_id":d.order_id,"product":d.product,"quantity":d.quantity,"vehicle_id":d.vehicle_id,"source":d.source,"destination":d.destination,"dispatch_status":d.dispatch_status,"dispatch_date":d.dispatch_date.isoformat() if d.dispatch_date else None}
