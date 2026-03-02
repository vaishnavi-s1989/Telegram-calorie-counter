"""
Food service for parsing and nutrition lookup
"""
import re
from typing import List, Dict, Tuple
from datetime import datetime
from src.models.schemas import FoodItem, FoodEntry, NutritionInfo


class FoodService:
    """Service for food parsing and nutrition calculations"""
    
    def __init__(self):
        # Mock nutrition database (Indian foods optimized)
        self.nutrition_db = {
            'egg': {'calories': 70, 'protein': 6, 'carbs': 1, 'fats': 5, 'unit': 'piece'},
            'eggs': {'calories': 70, 'protein': 6, 'carbs': 1, 'fats': 5, 'unit': 'piece'},
            'dosa': {'calories': 120, 'protein': 3, 'carbs': 22, 'fats': 2, 'unit': 'piece'},
            'idli': {'calories': 39, 'protein': 2, 'carbs': 8, 'fats': 0.5, 'unit': 'piece'},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fats': 0.3, 'unit': 'cup'},
            'roti': {'calories': 71, 'protein': 3, 'carbs': 15, 'fats': 0.4, 'unit': 'piece'},
            'chapati': {'calories': 71, 'protein': 3, 'carbs': 15, 'fats': 0.4, 'unit': 'piece'},
            'dal': {'calories': 115, 'protein': 9, 'carbs': 20, 'fats': 0.4, 'unit': 'cup'},
            'chicken': {'calories': 165, 'protein': 31, 'carbs': 0, 'fats': 3.6, 'unit': '100g'},
            'paneer': {'calories': 265, 'protein': 18, 'carbs': 3, 'fats': 20, 'unit': '100g'},
            'milk': {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fats': 1, 'unit': '100ml'},
            'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fats': 0.3, 'unit': 'piece'},
            'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fats': 0.2, 'unit': 'piece'},
            'toast': {'calories': 79, 'protein': 2.5, 'carbs': 15, 'fats': 1, 'unit': 'slice'},
            'bread': {'calories': 79, 'protein': 2.5, 'carbs': 15, 'fats': 1, 'unit': 'slice'},
            'butter': {'calories': 102, 'protein': 0.1, 'carbs': 0, 'fats': 11.5, 'unit': 'tbsp'},
            'ghee': {'calories': 112, 'protein': 0, 'carbs': 0, 'fats': 12.7, 'unit': 'tbsp'},
            'samosa': {'calories': 262, 'protein': 4, 'carbs': 24, 'fats': 17, 'unit': 'piece'},
            'paratha': {'calories': 126, 'protein': 3, 'carbs': 18, 'fats': 5, 'unit': 'piece'},
            'upma': {'calories': 150, 'protein': 4, 'carbs': 25, 'fats': 4, 'unit': 'cup'},
        }
    
    def parse_food_text(self, food_text: str) -> List[Tuple[float, str]]:
        """
        Parse food text to extract quantities and food names
        Returns: List of (quantity, food_name) tuples
        """
        # Pattern to match: number + optional unit + food name
        # Examples: "2 eggs", "1 cup rice", "150g chicken"
        pattern = r'(\d+(?:\.\d+)?)\s*(?:cups?|pieces?|slices?|g|grams?|ml|tbsp|tsp)?\s*([a-zA-Z\s]+)'
        
        matches = re.findall(pattern, food_text.lower())
        
        if not matches:
            # If no quantity found, assume 1 serving
            words = food_text.lower().split()
            return [(1.0, word) for word in words if word in self.nutrition_db]
        
        parsed_items = []
        for quantity_str, food_name in matches:
            quantity = float(quantity_str)
            food_name = food_name.strip()
            
            # Check if food exists in database
            if food_name in self.nutrition_db:
                parsed_items.append((quantity, food_name))
        
        return parsed_items
    
    def get_nutrition(self, food_name: str, quantity: float = 1.0) -> Dict:
        """
        Get nutrition information for a food item
        """
        if food_name.lower() not in self.nutrition_db:
            # Return default values for unknown foods
            return {
                'calories': 100,
                'protein': 5,
                'carbs': 15,
                'fats': 3,
                'unit': 'serving'
            }
        
        base_nutrition = self.nutrition_db[food_name.lower()]
        
        return {
            'calories': base_nutrition['calories'] * quantity,
            'protein': base_nutrition['protein'] * quantity,
            'carbs': base_nutrition['carbs'] * quantity,
            'fats': base_nutrition['fats'] * quantity,
            'unit': base_nutrition['unit']
        }
    
    def create_food_entry(
        self,
        telegram_user_id: int,
        food_text: str
    ) -> FoodEntry:
        """
        Create a food entry from text input
        """
        # Parse the food text
        parsed_items = self.parse_food_text(food_text)
        
        if not parsed_items:
            # If parsing fails, create a default entry
            parsed_items = [(1.0, 'unknown food')]
        
        # Create food items with nutrition
        food_items = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for quantity, food_name in parsed_items:
            nutrition = self.get_nutrition(food_name, quantity)
            
            food_item = FoodItem(
                name=f"{quantity} {food_name}",
                quantity=quantity,
                unit=nutrition['unit'],
                nutrition=NutritionInfo(
                    calories=nutrition['calories'],
                    protein=nutrition['protein'],
                    carbs=nutrition['carbs'],
                    fats=nutrition['fats']
                )
            )
            
            food_items.append(food_item)
            total_calories += nutrition['calories']
            total_protein += nutrition['protein']
            total_carbs += nutrition['carbs']
            total_fats += nutrition['fats']
        
        # Create the food entry
        entry = FoodEntry(
            telegram_user_id=telegram_user_id,
            date=datetime.now(),
            food_text=food_text,
            items=food_items,
            total_nutrition=NutritionInfo(
                calories=round(total_calories, 1),
                protein=round(total_protein, 1),
                carbs=round(total_carbs, 1),
                fats=round(total_fats, 1)
            ),
            timestamp=datetime.now()
        )
        
        return entry
    
    def calculate_daily_total(self, entries: List[FoodEntry]) -> NutritionInfo:
        """
        Calculate total nutrition from multiple entries
        """
        total_calories = sum(e.total_nutrition.calories for e in entries)
        total_protein = sum(e.total_nutrition.protein for e in entries)
        total_carbs = sum(e.total_nutrition.carbs for e in entries)
        total_fats = sum(e.total_nutrition.fats for e in entries)
        
        return NutritionInfo(
            calories=round(total_calories, 1),
            protein=round(total_protein, 1),
            carbs=round(total_carbs, 1),
            fats=round(total_fats, 1)
        )

# Made with Bob
