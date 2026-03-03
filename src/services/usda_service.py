"""
USDA FoodData Central API Service
Handles food search and nutrition data retrieval from USDA database
"""
import requests
from typing import Optional, List, Dict, Any
from config import config
import logging

logger = logging.getLogger(__name__)


class USDAService:
    """Service for interacting with USDA FoodData Central API"""
    
    def __init__(self):
        self.api_key = config.USDA_API_KEY
        self.base_url = config.USDA_API_URL
        
        if not self.api_key:
            logger.warning("USDA_API_KEY not configured. Food lookups will fail.")
    
    def search_foods(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """
        Search for foods in USDA database
        
        Args:
            query: Search term (e.g., "chicken breast", "apple")
            page_size: Number of results to return (default 5)
            
        Returns:
            List of food items with basic info
        """
        if not self.api_key:
            logger.error("USDA API key not configured")
            return []
        
        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            foods = data.get("foods", [])
            logger.info(f"Found {len(foods)} results for query: {query}")
            return foods
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching USDA API: {e}")
            return []
    
    def get_food_details(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed nutrition information for a specific food
        
        Args:
            fdc_id: FoodData Central ID
            
        Returns:
            Detailed food information including all nutrients
        """
        if not self.api_key:
            logger.error("USDA API key not configured")
            return None
        
        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching food details for FDC ID {fdc_id}: {e}")
            return None
    
    def extract_nutrition(self, food_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key nutrition values from USDA food data
        
        Args:
            food_data: Raw food data from USDA API
            
        Returns:
            Dictionary with calories, protein, carbs, fats per 100g
        """
        nutrition = {
            "calories": 0.0,
            "protein": 0.0,
            "carbs": 0.0,
            "fats": 0.0,
        }
        
        # Nutrient IDs in USDA database
        nutrient_map = {
            1008: "calories",      # Energy (kcal)
            1003: "protein",       # Protein (g)
            1005: "carbs",         # Carbohydrate, by difference (g)
            1004: "fats",          # Total lipid (fat) (g)
        }
        
        # Extract from foodNutrients array
        food_nutrients = food_data.get("foodNutrients", [])
        
        for nutrient in food_nutrients:
            nutrient_id = nutrient.get("nutrient", {}).get("id")
            if nutrient_id in nutrient_map:
                key = nutrient_map[nutrient_id]
                value = nutrient.get("amount", 0.0)
                nutrition[key] = round(float(value), 2)
        
        return nutrition
    
    def search_and_get_nutrition(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a food and return the best match with nutrition info
        
        Args:
            food_name: Name of the food to search for
            
        Returns:
            Dictionary with food name, description, and nutrition per 100g
        """
        # Search for the food
        results = self.search_foods(food_name, page_size=1)
        
        if not results:
            logger.warning(f"No results found for: {food_name}")
            return None
        
        # Get the first (best) match
        best_match = results[0]
        fdc_id = best_match.get("fdcId")
        
        if not fdc_id:
            logger.error(f"No FDC ID found for: {food_name}")
            return None
        
        # Get detailed nutrition info
        food_details = self.get_food_details(fdc_id)
        
        if not food_details:
            return None
        
        # Extract nutrition values
        nutrition = self.extract_nutrition(food_details)
        
        return {
            "fdc_id": fdc_id,
            "name": food_details.get("description", food_name),
            "brand": food_details.get("brandOwner", ""),
            "data_type": food_details.get("dataType", ""),
            "nutrition_per_100g": nutrition,
        }
    
    def get_nutrition_for_quantity(
        self, 
        food_name: str, 
        quantity: float, 
        unit: str = "g"
    ) -> Optional[Dict[str, Any]]:
        """
        Get nutrition for a specific quantity of food
        
        Args:
            food_name: Name of the food
            quantity: Amount (default assumes grams)
            unit: Unit of measurement (g, oz, cup, etc.)
            
        Returns:
            Dictionary with nutrition values for the specified quantity
        """
        food_data = self.search_and_get_nutrition(food_name)
        
        if not food_data:
            return None
        
        nutrition_per_100g = food_data["nutrition_per_100g"]
        
        # Convert quantity to grams if needed
        # For now, assume quantity is in grams or use simple conversions
        quantity_in_grams = quantity
        
        # Simple unit conversions (approximate)
        unit_conversions = {
            "oz": 28.35,
            "lb": 453.592,
            "cup": 240,  # Approximate for liquids
            "tbsp": 15,
            "tsp": 5,
        }
        
        if unit.lower() in unit_conversions:
            quantity_in_grams = quantity * unit_conversions[unit.lower()]
        
        # Calculate nutrition for the specified quantity
        multiplier = quantity_in_grams / 100.0
        
        return {
            "name": food_data["name"],
            "quantity": quantity,
            "unit": unit,
            "quantity_in_grams": round(quantity_in_grams, 2),
            "nutrition": {
                "calories": round(nutrition_per_100g["calories"] * multiplier, 1),
                "protein": round(nutrition_per_100g["protein"] * multiplier, 1),
                "carbs": round(nutrition_per_100g["carbs"] * multiplier, 1),
                "fats": round(nutrition_per_100g["fats"] * multiplier, 1),
            }
        }


# Singleton instance
usda_service = USDAService()

# Made with Bob
