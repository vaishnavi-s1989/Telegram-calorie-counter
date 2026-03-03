"""
Test script for USDA API integration
Run this to verify the USDA FoodData Central API is working correctly
"""
import sys
from src.services.usda_service import usda_service
from src.services.food_service import food_service
from config import config

def test_usda_api():
    """Test USDA API connection and basic functionality"""
    print("=" * 60)
    print("Testing USDA FoodData Central API Integration")
    print("=" * 60)
    
    # Check if API key is configured
    if not config.USDA_API_KEY:
        print("\n❌ ERROR: USDA_API_KEY is not configured!")
        print("Please set USDA_API_KEY in your .env file")
        print("Get your free API key at: https://fdc.nal.usda.gov/api-key-signup.html")
        return False
    
    print(f"\n✓ API Key configured: {config.USDA_API_KEY[:10]}...")
    print(f"✓ API URL: {config.USDA_API_URL}")
    
    # Test 1: Search for a food
    print("\n" + "-" * 60)
    print("Test 1: Searching for 'chicken breast'")
    print("-" * 60)
    
    results = usda_service.search_foods("chicken breast", page_size=3)
    
    if not results:
        print("❌ No results found. Check your API key and internet connection.")
        return False
    
    print(f"✓ Found {len(results)} results:")
    for i, food in enumerate(results, 1):
        print(f"  {i}. {food.get('description', 'N/A')} (FDC ID: {food.get('fdcId', 'N/A')})")
    
    # Test 2: Get detailed nutrition for first result
    print("\n" + "-" * 60)
    print("Test 2: Getting nutrition details for first result")
    print("-" * 60)
    
    first_food = results[0]
    fdc_id = first_food.get('fdcId')
    
    if fdc_id:
        details = usda_service.get_food_details(fdc_id)
        if details:
            nutrition = usda_service.extract_nutrition(details)
            print(f"✓ Nutrition per 100g:")
            print(f"  - Calories: {nutrition['calories']} kcal")
            print(f"  - Protein: {nutrition['protein']}g")
            print(f"  - Carbs: {nutrition['carbs']}g")
            print(f"  - Fats: {nutrition['fats']}g")
        else:
            print("❌ Failed to get food details")
            return False
    
    # Test 3: Search and get nutrition in one call
    print("\n" + "-" * 60)
    print("Test 3: Search and get nutrition for 'apple'")
    print("-" * 60)
    
    apple_data = usda_service.search_and_get_nutrition("apple")
    
    if apple_data:
        print(f"✓ Food: {apple_data['name']}")
        print(f"  Data Type: {apple_data['data_type']}")
        print(f"  Nutrition per 100g:")
        nutrition = apple_data['nutrition_per_100g']
        print(f"  - Calories: {nutrition['calories']} kcal")
        print(f"  - Protein: {nutrition['protein']}g")
        print(f"  - Carbs: {nutrition['carbs']}g")
        print(f"  - Fats: {nutrition['fats']}g")
    else:
        print("❌ Failed to get apple nutrition")
        return False
    
    # Test 4: Get nutrition for specific quantity
    print("\n" + "-" * 60)
    print("Test 4: Get nutrition for '150g chicken breast'")
    print("-" * 60)
    
    quantity_result = usda_service.get_nutrition_for_quantity("chicken breast", 150, "g")
    
    if quantity_result:
        print(f"✓ Food: {quantity_result['name']}")
        print(f"  Quantity: {quantity_result['quantity']}{quantity_result['unit']}")
        print(f"  Nutrition:")
        nutrition = quantity_result['nutrition']
        print(f"  - Calories: {nutrition['calories']} kcal")
        print(f"  - Protein: {nutrition['protein']}g")
        print(f"  - Carbs: {nutrition['carbs']}g")
        print(f"  - Fats: {nutrition['fats']}g")
    else:
        print("❌ Failed to get nutrition for quantity")
        return False
    
    # Test 5: Test FoodService integration
    print("\n" + "-" * 60)
    print("Test 5: Testing FoodService with '2 eggs and 100g chicken'")
    print("-" * 60)
    
    entry = food_service.create_food_entry(
        telegram_user_id=12345,
        food_text="2 eggs and 100g chicken"
    )
    
    print(f"✓ Created food entry:")
    print(f"  Total Nutrition:")
    print(f"  - Calories: {entry.total_nutrition.calories} kcal")
    print(f"  - Protein: {entry.total_nutrition.protein}g")
    print(f"  - Carbs: {entry.total_nutrition.carbs}g")
    print(f"  - Fats: {entry.total_nutrition.fats}g")
    print(f"\n  Individual items:")
    for item in entry.items:
        print(f"  - {item.name}: {item.nutrition.calories} kcal")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! USDA API integration is working.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_usda_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
