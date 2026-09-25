import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
DATABASE_URL = os.getenv('DATABASE_URL', '').strip() or f"sqlite:///{os.path.join(BASE_DIR, 'sih26179_mvp.db')}"
IS_POSTGRES = DATABASE_URL.startswith(('postgresql://', 'postgresql+psycopg2://', 'postgres://'))
connect_args = {'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    id = Column(Integer, primary_key=True)
    order_id = Column(String(40), unique=True, nullable=False, index=True)
    product = Column(String(80), nullable=False)
    store = Column(String(40), nullable=False)
    retailer = Column(String(120), default='Retail Store 1')
    factory = Column(String(120), default='Factory A')
    quantity = Column(Integer, nullable=False)
    priority = Column(String(30), default='HIGH')
    status = Column(String(40), default='PENDING')
    created_at = Column(DateTime, default=datetime.utcnow)
    expected_date = Column(String(20), nullable=True)

class ProductionOrder(Base):
    __tablename__ = 'production_orders'
    id = Column(Integer, primary_key=True)
    order_id = Column(String(40), unique=True, nullable=False, index=True)
    product = Column(String(80), nullable=False)
    order_quantity = Column(Integer, nullable=False)
    finished_stock = Column(Integer, default=0)
    production_required = Column(Integer, default=0)
    capacity = Column(Integer, default=0)
    raw_material_status = Column(String(40), default='SUFFICIENT')
    recommendation = Column(Text, default='')
    status = Column(String(40), default='PENDING')
    updated_at = Column(DateTime, default=datetime.utcnow)

class DispatchRecord(Base):
    __tablename__ = 'dispatch_records'
    id = Column(Integer, primary_key=True)
    order_id = Column(String(40), unique=True, nullable=False, index=True)
    product = Column(String(80), nullable=False)
    quantity = Column(Integer, nullable=False)
    vehicle_id = Column(String(40), default='DEMO-TRUCK-01')
    source = Column(String(120), default='Factory A')
    destination = Column(String(120), default='Retail Store 1')
    dispatch_status = Column(String(40), default='PENDING')
    dispatch_date = Column(DateTime, nullable=True)

class CustomerFeedback(Base):
    __tablename__ = 'customer_feedback'
    id = Column(Integer, primary_key=True)
    product = Column(String(80), nullable=False)
    rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=False)
    sentiment = Column(String(30), default='NEUTRAL')
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        print(f"[database] Workflow tables were not initialized: {exc}")

init_db()
