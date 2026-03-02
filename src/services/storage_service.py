"""
Storage service for managing user data and food entries
Currently uses in-memory storage, can be replaced with database later
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from src.models.schemas import User, FoodEntry, DailySummary, HistoryEntry, NutritionInfo


class StorageService:
    """Service for data storage and retrieval"""
    
    def __init__(self):
        # In-memory storage
        self.users: Dict[int, User] = {}
        self.food_entries: Dict[int, List[FoodEntry]] = {}
    
    # User operations
    def create_user(self, telegram_user_id: int, name: str, username: Optional[str] = None) -> User:
        """Create or update a user"""
        if telegram_user_id in self.users:
            user = self.users[telegram_user_id]
            user.last_active = datetime.now()
            return user
        
        user = User(
            telegram_user_id=telegram_user_id,
            name=name,
            username=username,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        self.users[telegram_user_id] = user
        return user
    
    def get_user(self, telegram_user_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        return self.users.get(telegram_user_id)
    
    # Food entry operations
    def add_food_entry(self, entry: FoodEntry) -> FoodEntry:
        """Add a food entry"""
        user_id = entry.telegram_user_id
        
        if user_id not in self.food_entries:
            self.food_entries[user_id] = []
        
        # Assign ID
        entry.id = len(self.food_entries[user_id]) + 1
        self.food_entries[user_id].append(entry)
        
        return entry
    
    def get_entries_by_date(
        self,
        telegram_user_id: int,
        date: datetime
    ) -> List[FoodEntry]:
        """Get all entries for a specific date"""
        if telegram_user_id not in self.food_entries:
            return []
        
        target_date = date.date()
        return [
            entry for entry in self.food_entries[telegram_user_id]
            if entry.date.date() == target_date
        ]
    
    def get_today_entries(self, telegram_user_id: int) -> List[FoodEntry]:
        """Get today's entries"""
        return self.get_entries_by_date(telegram_user_id, datetime.now())
    
    def get_entries_range(
        self,
        telegram_user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[FoodEntry]:
        """Get entries within a date range"""
        if telegram_user_id not in self.food_entries:
            return []
        
        start = start_date.date()
        end = end_date.date()
        
        return [
            entry for entry in self.food_entries[telegram_user_id]
            if start <= entry.date.date() <= end
        ]
    
    def delete_today_entries(self, telegram_user_id: int) -> int:
        """Delete all entries for today, returns count deleted"""
        if telegram_user_id not in self.food_entries:
            return 0
        
        today = datetime.now().date()
        original_count = len(self.food_entries[telegram_user_id])
        
        self.food_entries[telegram_user_id] = [
            entry for entry in self.food_entries[telegram_user_id]
            if entry.date.date() != today
        ]
        
        deleted_count = original_count - len(self.food_entries[telegram_user_id])
        return deleted_count
    
    def delete_entry(self, telegram_user_id: int, entry_id: int) -> bool:
        """Delete a specific entry"""
        if telegram_user_id not in self.food_entries:
            return False
        
        original_count = len(self.food_entries[telegram_user_id])
        self.food_entries[telegram_user_id] = [
            entry for entry in self.food_entries[telegram_user_id]
            if entry.id != entry_id
        ]
        
        return len(self.food_entries[telegram_user_id]) < original_count
    
    # Summary operations
    def get_daily_summary(self, telegram_user_id: int, date: datetime) -> DailySummary:
        """Get summary for a specific day"""
        entries = self.get_entries_by_date(telegram_user_id, date)
        
        total_calories = sum(e.total_nutrition.calories for e in entries)
        total_protein = sum(e.total_nutrition.protein for e in entries)
        total_carbs = sum(e.total_nutrition.carbs for e in entries)
        total_fats = sum(e.total_nutrition.fats for e in entries)
        
        return DailySummary(
            telegram_user_id=telegram_user_id,
            date=date,
            total_calories=round(total_calories, 1),
            total_protein=round(total_protein, 1),
            total_carbs=round(total_carbs, 1),
            total_fats=round(total_fats, 1),
            entry_count=len(entries)
        )
    
    def get_history(self, telegram_user_id: int, days: int = 7) -> List[HistoryEntry]:
        """Get history for the last N days"""
        history = []
        today = datetime.now()
        
        for i in range(days):
            date = today - timedelta(days=i)
            summary = self.get_daily_summary(telegram_user_id, date)
            
            history.append(HistoryEntry(
                date=date,
                calories=summary.total_calories,
                protein=summary.total_protein,
                carbs=summary.total_carbs,
                fats=summary.total_fats,
                entry_count=summary.entry_count
            ))
        
        return history
    
    def get_total_entries_count(self, telegram_user_id: int) -> int:
        """Get total number of entries for a user"""
        if telegram_user_id not in self.food_entries:
            return 0
        return len(self.food_entries[telegram_user_id])

# Made with Bob
