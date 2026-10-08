"""
VIT MAPATHON — Member 3 Backend Database Connection Manager
Provides PostgreSQL / PostGIS connection pooling and automatic graceful fallback
to Member 1 / Member 3 GeoJSON and JSON artifacts when database is offline.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("DatabaseManager")

# Configurable database URL
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

DEFAULT_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

Base = declarative_base()

_engine = None
_SessionLocal = None
_db_available = False


def init_db_connection() -> bool:
    """Tests connection to PostgreSQL/PostGIS and verifies table presence."""
    global _engine, _SessionLocal, _db_available
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            # Check if postgis extension and table exist
            res = conn.execute(text("SELECT to_regclass('public.agricultural_parcels');")).scalar()
            if res is not None:
                # Check record count
                count = conn.execute(text("SELECT COUNT(*) FROM agricultural_parcels;")).scalar()
                if count and count > 0:
                    _engine = engine
                    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
                    _db_available = True
                    logger.info(f"PostGIS database connected. Ingested parcels in DB: {count}")
                    return True
                else:
                    logger.warning("Table 'agricultural_parcels' exists in DB but is empty. Using GeoJSON file fallback.")
            else:
                logger.info("Table 'agricultural_parcels' not found in PostGIS. Using GeoJSON file fallback.")
    except Exception as e:
        logger.info(f"PostGIS connection not established ({e}). Running in offline GeoJSON fallback mode.")

    _db_available = False
    return False


def is_db_connected() -> bool:
    """Returns True if PostGIS database is active and has parcel records."""
    global _db_available
    return _db_available


def get_db():
    """Dependency for acquiring a database session."""
    if not is_db_connected():
        yield None
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def resolve_artifact_path(filename: str) -> Optional[str]:
    """
    Resolves data files according to team contract:
    1. Checks member1-ml/outputs/<filename>
    2. Checks member3-fullstack/inputs/<filename>
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    member3_dir = os.path.dirname(backend_dir)
    repo_root = os.path.dirname(member3_dir)

    candidates = [
        os.path.join(repo_root, "member1-ml", "outputs", filename),
        os.path.join(member3_dir, "inputs", filename),
    ]

    for cand in candidates:
        if os.path.exists(cand):
            return cand

    return None


def load_json_artifact(filename: str) -> Dict[str, Any]:
    """Loads a JSON deliverable from resolved candidate paths."""
    path = resolve_artifact_path(filename)
    if not path:
        raise FileNotFoundError(f"Artifact {filename} could not be located in member1-ml/outputs or member3-fullstack/inputs.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
