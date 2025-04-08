import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment variable or use default
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb://localhost:27017/meeting_assistant")

# Create engine
if DATABASE_URL.startswith("mongodb"):
    # MongoDB connection
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # For MongoDB, we'll use Motor directly
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client.get_database()
    
    # SQLAlchemy is not used directly with MongoDB, but we'll keep the interface similar
    engine = None
    SessionLocal = None
    Base = None
    
    def get_db():
        return db
    
    def init_db():
        # Create collections if they don't exist
        collections = ["sessions", "transcripts", "responses"]
        for collection in collections:
            if collection not in db.list_collection_names():
                db.create_collection(collection)
else:
    # SQL database connection (SQLite, PostgreSQL, etc.)
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def init_db():
        Base.metadata.create_all(bind=engine)