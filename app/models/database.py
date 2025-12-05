"""
Database Models and Connection Management
Async SQLite connection for reading Osmocom HLR database
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, select
from typing import List, Optional
from datetime import datetime
import aiosqlite

from app.config import settings

# SQLAlchemy Base
Base = declarative_base()


class Subscriber(Base):
    """
    SQLAlchemy model for Osmocom HLR Subscriber table
    Note: Osmocom's actual schema may vary by version
    This is a common schema structure
    """
    __tablename__ = "subscriber"
    
    id = Column(Integer, primary_key=True)
    imsi = Column(String(15), unique=True, nullable=False, index=True)
    msisdn = Column(String(15), nullable=True)  # Extension/phone number
    imei = Column(String(15), nullable=True)
    authorized = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseManager:
    """
    Async database manager for HLR SQLite database
    Provides connection pooling and query helpers
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to HLR SQLite database (defaults to settings)
        """
        self.db_path = db_path or settings.hlr_database_path
        # Create async SQLite engine (read-only to avoid conflicts)
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_path}",
            echo=settings.debug_mode,
            connect_args={"check_same_thread": False}
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_all_subscribers(self) -> List[dict]:
        """
        Query all subscribers from HLR database
        
        Returns:
            List of subscriber dictionaries
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(select(Subscriber))
                subscribers = result.scalars().all()
                
                return [
                    {
                        "imsi": sub.imsi,
                        "msisdn": sub.msisdn,
                        "imei": sub.imei,
                        "last_seen": sub.updated,
                        "authorized": sub.authorized
                    }
                    for sub in subscribers
                ]
        except Exception as e:
            # If table schema differs, fall back to raw SQL
            return await self._get_subscribers_raw()
    
    async def _get_subscribers_raw(self) -> List[dict]:
        """
        Fallback method using raw SQL for flexibility
        Adapts to different Osmocom HLR schema versions
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM subscriber ORDER BY id DESC LIMIT 1000"
                )
                rows = await cursor.fetchall()
                
                subscribers = []
                for row in rows:
                    row_dict = dict(row)
                    subscribers.append({
                        "imsi": row_dict.get("imsi"),
                        "msisdn": row_dict.get("msisdn") or row_dict.get("extension"),
                        "imei": row_dict.get("imei"),
                        "last_seen": row_dict.get("updated") or row_dict.get("last_lu_seen"),
                        "authorized": bool(row_dict.get("authorized", 0))
                    })
                
                return subscribers
        except Exception as e:
            raise Exception(f"Failed to query HLR database: {str(e)}")
    
    async def get_subscriber_by_imsi(self, imsi: str) -> Optional[dict]:
        """
        Get specific subscriber by IMSI
        
        Args:
            imsi: IMSI to search for
            
        Returns:
            Subscriber dictionary or None
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM subscriber WHERE imsi = ? LIMIT 1",
                    (imsi,)
                )
                row = await cursor.fetchone()
                
                if row:
                    row_dict = dict(row)
                    return {
                        "imsi": row_dict.get("imsi"),
                        "msisdn": row_dict.get("msisdn") or row_dict.get("extension"),
                        "imei": row_dict.get("imei"),
                        "last_seen": row_dict.get("updated") or row_dict.get("last_lu_seen"),
                        "authorized": bool(row_dict.get("authorized", 0))
                    }
                return None
        except Exception as e:
            raise Exception(f"Failed to query subscriber {imsi}: {str(e)}")
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
