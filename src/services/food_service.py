"""
Food service for parsing and nutrition lookup using USDA FoodData Central API
"""
import re
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from src.models.schemas import FoodItem, FoodEntry, NutritionInfo
from src.services.usda_service import usda_service

logger = logging.getLogger(__name__)


class FoodService:
    """Service for food parsing and nutrition calculations using USDA API"""
    
    def __init__(self):
        self.usda = usda_service
        
        # Fallback nutrition database for common items when API fails
        # or for quick lookups of very common foods
        self.fallback_db = {
            'egg': {'calories': 70, 'protein': 6, 'carbs': 1, 'fats': 5, 'unit': 'piece', 'grams': 50},
            'eggs': {'calories': 70, 'protein': 6, 'carbs': 1, 'fats': 5, 'unit': 'piece', 'grams': 50},
            'dosa': {'calories': 120, 'protein': 3, 'carbs': 22, 'fats': 2, 'unit': 'piece', 'grams': 100},
            'idli': {'calories': 39, 'protein': 2, 'carbs': 8, 'fats': 0.5, 'unit': 'piece', 'grams': 30},
            'rice': {'calories': 130, 'protein': 2.7, 'carbs': 28, 'fats': 0.3, 'unit': 'cup', 'grams': 100},
            'roti': {'calories': 71, 'protein': 3, 'carbs': 15, 'fats': 0.4, 'unit': 'piece', 'grams': 40},
            'chapati': {'calories': 71, 'protein': 3, 'carbs': 15, 'fats': 0.4, 'unit': 'piece', 'grams': 40},
            'dal': {'calories': 115, 'protein': 9, 'carbs': 20, 'fats': 0.4, 'unit': 'cup', 'grams': 200},
            'paneer': {'calories': 265, 'protein': 18, 'carbs': 3, 'fats': 20, 'unit': '100g', 'grams': 100},
            'milk': {'calories': 42, 'protein': 3.4, 'carbs': 5, 'fats': 1, 'unit': '100ml', 'grams': 100},
            'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fats': 0.3, 'unit': 'piece', 'grams': 100},
            'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fats': 0.2, 'unit': 'piece', 'grams': 100},
            'toast': {'calories': 79, 'protein': 2.5, 'carbs': 15, 'fats': 1, 'unit': 'slice', 'grams': 30},
            'bread': {'calories': 79, 'protein': 2.5, 'carbs': 15, 'fats': 1, 'unit': 'slice', 'grams': 30},
            'butter': {'calories': 102, 'protein': 0.1, 'carbs': 0, 'fats': 11.5, 'unit': 'tbsp', 'grams': 14},
            'ghee': {'calories': 112, 'protein': 0, 'carbs': 0, 'fats': 12.7, 'unit': 'tbsp', 'grams': 14},
            'samosa': {'calories': 262, 'protein': 4, 'carbs': 24, 'fats': 17, 'unit': 'piece', 'grams': 100},
            'paratha': {'calories': 126, 'protein': 3, 'carbs': 18, 'fats': 5, 'unit': 'piece', 'grams': 50},
            'upma': {'calories': 150, 'protein': 4, 'carbs': 25, 'fats': 4, 'unit': 'cup', 'grams': 200},
        }
    
    def parse_food_text(self, food_text: str) -> List[Tuple[float, str, str]]:
        """
        Parse food text to extract quantities, units, and food names
        Returns: List of (quantity, unit, food_name) tuples
        
        Examples:
            "2 eggs" -> [(2.0, 'piece', 'eggs')]
            "150g chicken" -> [(150.0, 'g', 'chicken')]
            "1 cup rice" -> [(1.0, 'cup', 'rice')]
        """
        # Pattern to match: number + optional unit + food name
        pattern = r'(\d+(?:\.\d+)?)\s*(cups?|pieces?|slices?|g|grams?|ml|oz|tbsp|tsp)?\s*([a-zA-Z\s]+)'
        
        matches = re.findall(pattern, food_text.lower())
        
        if not matches:
            # If no quantity found, assume 1 serving
            words = food_text.lower().split()
            return [(1.0, 'serving', word) for word in words if len(word) > 2]
        
        parsed_items = []
        for quantity_str, unit, food_name in matches:
            quantity = float(quantity_str)
            food_name = food_name.strip()
            unit = unit.strip() if unit else 'serving'
            
            # Normalize unit names
            if unit in ['gram', 'grams']:
                unit = 'g'
            elif unit in ['cup', 'cups']:
                unit = 'cup'
            elif unit in ['piece', 'pieces']:
                unit = 'piece'
            
            if food_name:
                parsed_items.append((quantity, unit, food_name))
        
        return parsed_items
    
    def get_nutrition_from_usda(
        self, 
        food_name: str, 
        quantity: float, 
        unit: str
    ) -> Optional[Dict]:
        """
        Get nutrition information from USDA API
        """
        try:
            # For piece/serving units, try to estimate grams
            if unit in ['piece', 'serving']:
                # Check if we have a fallback estimate
                if food_name in self.fallback_db:
                    estimated_grams = self.fallback_db[food_name]['grams'] * quantity
                    result = self.usda.get_nutrition_for_quantity(food_name, estimated_grams, 'g')
                else:
                    # Use 100g as default serving size
                    result = self.usda.get_nutrition_for_quantity(food_name, 100 * quantity, 'g')
            else:
                result = self.usda.get_nutrition_for_quantity(food_name, quantity, unit)
            
            if result:
                return {
                    'calories': result['nutrition']['calories'],
                    'protein': result['nutrition']['protein'],
                    'carbs': result['nutrition']['carbs'],
                    'fats': result['nutrition']['fats'],
                    'unit': unit,
                    'source': 'usda'
                }
        except Exception as e:
            logger.error(f"Error fetching from USDA API for {food_name}: {e}")
        
        return None
    
    def get_nutrition_from_fallback(
        self, 
        food_name: str, 
        quantity: float
    ) -> Dict:
        """
        Get nutrition from fallback database
        """
        if food_name.lower() in self.fallback_db:
            base_nutrition = self.fallback_db[food_name.lower()]
            return {
                'calories': base_nutrition['calories'] * quantity,
                'protein': base_nutrition['protein'] * quantity,
                'carbs': base_nutrition['carbs'] * quantity,
                'fats': base_nutrition['fats'] * quantity,
                'unit': base_nutrition['unit'],
                'source': 'fallback'
            }
        
        # Return default values for completely unknown foods
        return {
            'calories': 100 * quantity,
            'protein': 5 * quantity,
            'carbs': 15 * quantity,
            'fats': 3 * quantity,
            'unit': 'serving',
            'source': 'default'
        }
    
    def get_nutrition(
        self, 
        food_name: str, 
        quantity: float = 1.0, 
        unit: str = 'serving'
    ) -> Dict:
        """
        Get nutrition information for a food item
        Tries USDA API first, falls back to local database
        """
        # Try USDA API first
        usda_result = self.get_nutrition_from_usda(food_name, quantity, unit)
        
        if usda_result:
            logger.info(f"Got nutrition for '{food_name}' from USDA API")
            return usda_result
        
        # Fall back to local database
        logger.info(f"Using fallback database for '{food_name}'")
        return self.get_nutrition_from_fallback(food_name, quantity)
    
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
            parsed_items = [(1.0, 'serving', 'unknown food')]
        
        # Create food items with nutrition
        food_items = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for quantity, unit, food_name in parsed_items:
            nutrition = self.get_nutrition(food_name, quantity, unit)
            
            # Format the display name
            if unit == 'g':
                display_name = f"{quantity}g {food_name}"
            elif unit == 'serving':
                display_name = f"{quantity} {food_name}"
            else:
                display_name = f"{quantity} {unit} {food_name}"
            
            food_item = FoodItem(
                name=display_name,
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


# Singleton instance
food_service = FoodService()

# Made with Bob
