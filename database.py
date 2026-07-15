import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Hybrid Database Connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Writable temp directory for SQLite on serverless environments
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        DATABASE_URL = "sqlite:////tmp/database.db"
    else:
        DATABASE_URL = "sqlite:///./database.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
