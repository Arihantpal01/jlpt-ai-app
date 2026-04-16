from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 🔥 IMPORTANT: For Neon use sslmode=require
DATABASE_URL = "postgresql://neondb_owner:npg_6LMY1tlyJCmK@ep-quiet-sound-am30hlts.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()