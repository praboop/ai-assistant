from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add path to config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../embedding-service')))
from config import DB_CONFIG


DATABASE_URL = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)