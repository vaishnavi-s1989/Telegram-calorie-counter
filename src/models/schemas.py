"""
Data models and schemas for the application
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NutritionInfo(BaseModel):
    """Nutrition information for a food item"""
    calories: float = Field(..., description="Calories in kcal")
    protein: float = Field(..., description="Protein in grams")
    carbs: float = Field(..., description="Carbohydrates in grams")
    fats: float = Field(..., description="Fats in grams")


class FoodItem(BaseModel):
    """Individual food item"""
    name: str = Field(..., description="Name of the food item")
    quantity: float = Field(..., description="Quantity/serving size")
    unit: str = Field(default="serving", description="Unit of measurement")
    nutrition: NutritionInfo


class FoodEntry(BaseModel):
    """Food entry logged by user"""
    id: Optional[int] = None
    telegram_user_id: int
    date: datetime
    food_text: str = Field(..., description="Original text input by user")
    items: List[FoodItem]
    total_nutrition: NutritionInfo
    timestamp: datetime = Field(default_factory=datetime.now)


class DailySummary(BaseModel):
    """Daily nutrition summary"""
    telegram_user_id: int
    date: datetime
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fats: float
    entry_count: int = 0


class User(BaseModel):
    """User model"""
    telegram_user_id: int
    name: str
    username: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)


class HistoryEntry(BaseModel):
    """History entry for a specific date"""
    date: datetime
    calories: float
    protein: float
    carbs: float
    fats: float
    entry_count: int


class LogFoodRequest(BaseModel):
    """Request to log food"""
    telegram_user_id: int
    food_text: str


class LogFoodResponse(BaseModel):
    """Response after logging food"""
    success: bool
    message: str
    entry: Optional[FoodEntry] = None
    daily_total: Optional[NutritionInfo] = None

# Made with Bob
