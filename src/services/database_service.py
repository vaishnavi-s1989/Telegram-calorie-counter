"""
Database service — supports SQLite (local dev) and PostgreSQL (IBM Cloud).

The active backend is chosen automatically from DATABASE_URL in config:
  - sqlite:///...          → SQLite  (default, local development)
  - postgresql://...       → PostgreSQL via psycopg2 (IBM Databases for PostgreSQL)

IBM Cloud note:
  IBM Databases for PostgreSQL requires SSL.  Add ?sslmode=require to the
  connection string, or set PGSSLMODE=require as an environment variable.
  The full DATABASE_URL from the IBM Cloud service credentials looks like:
    postgresql://ibm_user:password@host:port/ibmclouddb?sslmode=require
"""
import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    text,
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    Text,
    Index,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import config
from src.models.schemas import User, FoodEntry, DailySummary, HistoryEntry, NutritionInfo, FoodItem

logger = logging.getLogger(__name__)

Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------

class UserORM(Base):
    __tablename__ = "users"

    telegram_user_id = Column(BigInteger, primary_key=True)
    name             = Column(String(255), nullable=False)
    username         = Column(String(255), nullable=True)
    created_at       = Column(String(50), nullable=False)
    last_active      = Column(String(50), nullable=False)


class FoodEntryORM(Base):
    __tablename__ = "food_entries"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id = Column(BigInteger, nullable=False)
    date             = Column(String(50), nullable=False)
    food_text        = Column(Text, nullable=False)
    items_json       = Column(Text, nullable=False)
    total_calories   = Column(Float, nullable=False)
    total_protein    = Column(Float, nullable=False)
    total_carbs      = Column(Float, nullable=False)
    total_fats       = Column(Float, nullable=False)
    timestamp        = Column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_user_date",      "telegram_user_id", "date"),
        Index("idx_user_timestamp", "telegram_user_id", "timestamp"),
    )


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------

def _build_engine():
    """
    Create a SQLAlchemy engine appropriate for the configured DATABASE_URL.

    SQLite  → single-threaded StaticPool (safe for dev / testing).
    Postgres → connection pool with pre-ping (handles IBM Cloud idle timeouts).
    """
    url = config.DATABASE_URL

    if config.is_postgres():
        logger.info("DatabaseService: connecting to PostgreSQL")
        engine = create_engine(
            url,
            pool_pre_ping=True,      # detect stale connections (IBM Cloud drops idle ones)
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,       # recycle connections every 30 min
            echo=config.DEBUG,
        )
    else:
        logger.info("DatabaseService: connecting to SQLite at %s", url)
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            url,
            connect_args=connect_args,
            poolclass=StaticPool,
            echo=config.DEBUG,
        )
        # Enable WAL mode for better concurrent read performance on SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


# ---------------------------------------------------------------------------
# DatabaseService
# ---------------------------------------------------------------------------

class DatabaseService:
    """
    Persistent storage service.

    Uses SQLAlchemy ORM so the same code works with both SQLite and
    PostgreSQL without any changes.
    """

    def __init__(self):
        self._engine = _build_engine()
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )
        self._init_database()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_database(self):
        """Create tables if they don't exist yet."""
        Base.metadata.create_all(bind=self._engine)
        logger.info("DatabaseService: tables initialised")

    def _get_session(self) -> Session:
        return self._SessionLocal()

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def create_user(
        self,
        telegram_user_id: int,
        name: str,
        username: Optional[str] = None,
    ) -> User:
        """Create or update a user (upsert)."""
        now = datetime.now().isoformat()

        with self._get_session() as session:
            existing = session.get(UserORM, telegram_user_id)
            if existing:
                existing.name        = name
                existing.username    = username
                existing.last_active = now
            else:
                session.add(UserORM(
                    telegram_user_id=telegram_user_id,
                    name=name,
                    username=username,
                    created_at=now,
                    last_active=now,
                ))
            session.commit()

        return User(
            telegram_user_id=telegram_user_id,
            name=name,
            username=username,
            created_at=datetime.fromisoformat(now),
            last_active=datetime.fromisoformat(now),
        )

    def get_user(self, telegram_user_id: int) -> Optional[User]:
        """Fetch a user by Telegram ID."""
        with self._get_session() as session:
            row = session.get(UserORM, telegram_user_id)
            if row:
                return User(
                    telegram_user_id=row.telegram_user_id,
                    name=row.name,
                    username=row.username,
                    created_at=datetime.fromisoformat(row.created_at),
                    last_active=datetime.fromisoformat(row.last_active),
                )
        return None

    # ------------------------------------------------------------------
    # Food entry operations
    # ------------------------------------------------------------------

    def add_food_entry(self, entry: FoodEntry) -> FoodEntry:
        """Persist a food entry and return it with its assigned id."""
        items_json = json.dumps([
            {
                "name":     item.name,
                "quantity": item.quantity,
                "unit":     item.unit,
                "nutrition": {
                    "calories": item.nutrition.calories,
                    "protein":  item.nutrition.protein,
                    "carbs":    item.nutrition.carbs,
                    "fats":     item.nutrition.fats,
                },
            }
            for item in entry.items
        ])

        orm_entry = FoodEntryORM(
            telegram_user_id=entry.telegram_user_id,
            date=entry.date.isoformat(),
            food_text=entry.food_text,
            items_json=items_json,
            total_calories=entry.total_nutrition.calories,
            total_protein=entry.total_nutrition.protein,
            total_carbs=entry.total_nutrition.carbs,
            total_fats=entry.total_nutrition.fats,
            timestamp=entry.timestamp.isoformat(),
        )

        with self._get_session() as session:
            session.add(orm_entry)
            session.commit()
            session.refresh(orm_entry)
            entry.id = orm_entry.id

        return entry

    def get_entries_by_date(
        self, telegram_user_id: int, date: datetime
    ) -> List[FoodEntry]:
        """Return all entries for a specific calendar date."""
        target_date = date.date().isoformat()

        with self._get_session() as session:
            rows = (
                session.query(FoodEntryORM)
                .filter(
                    FoodEntryORM.telegram_user_id == telegram_user_id,
                    # Cast to date for both SQLite and PostgreSQL
                    text("date(date) = date(:d)").bindparams(d=target_date)
                    if not config.is_postgres()
                    else text("CAST(date AS DATE) = CAST(:d AS DATE)").bindparams(d=target_date),
                )
                .order_by(FoodEntryORM.timestamp)
                .all()
            )
        return [self._orm_to_food_entry(r) for r in rows]

    def get_today_entries(self, telegram_user_id: int) -> List[FoodEntry]:
        """Return today's entries for a user."""
        return self.get_entries_by_date(telegram_user_id, datetime.now())

    def get_entries_range(
        self,
        telegram_user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[FoodEntry]:
        """Return entries within an inclusive date range."""
        start = start_date.date().isoformat()
        end   = end_date.date().isoformat()

        if config.is_postgres():
            date_filter = text(
                "CAST(date AS DATE) BETWEEN CAST(:s AS DATE) AND CAST(:e AS DATE)"
            ).bindparams(s=start, e=end)
        else:
            date_filter = text(
                "date(date) BETWEEN date(:s) AND date(:e)"
            ).bindparams(s=start, e=end)

        with self._get_session() as session:
            rows = (
                session.query(FoodEntryORM)
                .filter(
                    FoodEntryORM.telegram_user_id == telegram_user_id,
                    date_filter,
                )
                .order_by(FoodEntryORM.timestamp)
                .all()
            )
        return [self._orm_to_food_entry(r) for r in rows]

    def delete_today_entries(self, telegram_user_id: int) -> int:
        """Delete all of today's entries; returns the count deleted."""
        today = datetime.now().date().isoformat()

        if config.is_postgres():
            date_filter = text(
                "CAST(date AS DATE) = CAST(:d AS DATE)"
            ).bindparams(d=today)
        else:
            date_filter = text("date(date) = date(:d)").bindparams(d=today)

        with self._get_session() as session:
            rows = (
                session.query(FoodEntryORM)
                .filter(
                    FoodEntryORM.telegram_user_id == telegram_user_id,
                    date_filter,
                )
                .all()
            )
            count = len(rows)
            for row in rows:
                session.delete(row)
            session.commit()

        return count

    def delete_entry(self, telegram_user_id: int, entry_id: int) -> bool:
        """Delete a specific entry by id; returns True if deleted."""
        with self._get_session() as session:
            row = (
                session.query(FoodEntryORM)
                .filter(
                    FoodEntryORM.id == entry_id,
                    FoodEntryORM.telegram_user_id == telegram_user_id,
                )
                .first()
            )
            if row:
                session.delete(row)
                session.commit()
                return True
        return False

    # ------------------------------------------------------------------
    # Summary / history
    # ------------------------------------------------------------------

    def get_daily_summary(
        self, telegram_user_id: int, date: datetime
    ) -> DailySummary:
        """Aggregate nutrition totals for a single day."""
        entries = self.get_entries_by_date(telegram_user_id, date)

        return DailySummary(
            telegram_user_id=telegram_user_id,
            date=date,
            total_calories=round(sum(e.total_nutrition.calories for e in entries), 1),
            total_protein=round(sum(e.total_nutrition.protein  for e in entries), 1),
            total_carbs=round(sum(e.total_nutrition.carbs    for e in entries), 1),
            total_fats=round(sum(e.total_nutrition.fats     for e in entries), 1),
            entry_count=len(entries),
        )

    def get_history(
        self, telegram_user_id: int, days: int = 7
    ) -> List[HistoryEntry]:
        """Return per-day summaries for the last N days (newest first)."""
        from datetime import timedelta

        today   = datetime.now()
        history = []

        for i in range(days):
            day     = today - timedelta(days=i)
            summary = self.get_daily_summary(telegram_user_id, day)
            history.append(HistoryEntry(
                date=day,
                calories=summary.total_calories,
                protein=summary.total_protein,
                carbs=summary.total_carbs,
                fats=summary.total_fats,
                entry_count=summary.entry_count,
            ))

        return history

    def get_total_entries_count(self, telegram_user_id: int) -> int:
        """Return the total number of entries ever logged by a user."""
        with self._get_session() as session:
            return (
                session.query(FoodEntryORM)
                .filter(FoodEntryORM.telegram_user_id == telegram_user_id)
                .count()
            )

    # ------------------------------------------------------------------
    # Private conversion helper
    # ------------------------------------------------------------------

    def _orm_to_food_entry(self, row: FoodEntryORM) -> FoodEntry:
        items_data = json.loads(row.items_json)
        items = [
            FoodItem(
                name=item["name"],
                quantity=item["quantity"],
                unit=item["unit"],
                nutrition=NutritionInfo(**item["nutrition"]),
            )
            for item in items_data
        ]
        return FoodEntry(
            id=row.id,
            telegram_user_id=row.telegram_user_id,
            date=datetime.fromisoformat(row.date),
            food_text=row.food_text,
            items=items,
            total_nutrition=NutritionInfo(
                calories=row.total_calories,
                protein=row.total_protein,
                carbs=row.total_carbs,
                fats=row.total_fats,
            ),
            timestamp=datetime.fromisoformat(row.timestamp),
        )

# Made with Bob
