# USDA FoodData Central API Integration

This document explains how the WhatsApp Calorie Counter Bot integrates with the USDA FoodData Central API to provide accurate nutrition information.

## Overview

The bot now uses the **USDA FoodData Central API** instead of a local food database. This provides:

- ✅ Access to 300,000+ foods in the USDA database
- ✅ Accurate, government-verified nutrition data
- ✅ Support for branded foods, restaurant items, and generic foods
- ✅ Regular updates from USDA
- ✅ Free API access (with rate limits)

## Getting Started

### 1. Get Your USDA API Key

1. Visit: https://fdc.nal.usda.gov/api-key-signup.html
2. Fill out the signup form
3. You'll receive your API key via email instantly
4. The API key is **free** and has generous rate limits

### 2. Configure the API Key

Add your API key to the `.env` file:

```bash
# Copy the example file if you haven't already
cp .env.example .env

# Edit .env and add your API key
USDA_API_KEY=your_actual_api_key_here
```

### 3. Test the Integration

Run the test script to verify everything works:

```bash
python test_usda_integration.py
```

You should see output like:
```
============================================================
Testing USDA FoodData Central API Integration
============================================================

✓ API Key configured: abcd123456...
✓ API URL: https://api.nal.usda.gov/fdc/v1

------------------------------------------------------------
Test 1: Searching for 'chicken breast'
------------------------------------------------------------
✓ Found 3 results:
  1. Chicken, broilers or fryers, breast, meat only, cooked, roasted (FDC ID: 171477)
  ...

✅ All tests passed! USDA API integration is working.
```

## How It Works

### Architecture

```
User Input → FoodService → USDAService → USDA API
                ↓              ↓
           Fallback DB    Cache/Retry
```

### Components

#### 1. **USDAService** (`src/services/usda_service.py`)

Handles direct communication with the USDA API:

- `search_foods(query)` - Search for foods by name
- `get_food_details(fdc_id)` - Get detailed nutrition for a specific food
- `extract_nutrition(food_data)` - Parse nutrition values from API response
- `search_and_get_nutrition(food_name)` - Combined search + nutrition lookup
- `get_nutrition_for_quantity(food_name, quantity, unit)` - Calculate nutrition for specific amounts

#### 2. **FoodService** (`src/services/food_service.py`)

High-level service that:

- Parses user input (e.g., "2 eggs and 150g chicken")
- Calls USDAService for nutrition data
- Falls back to local database if API fails
- Creates FoodEntry objects for database storage

### Data Flow Example

**User Input:** "150g chicken breast"

1. **Parse:** Extract quantity (150), unit (g), food name (chicken breast)
2. **USDA Lookup:** Search for "chicken breast" in USDA database
3. **Get Nutrition:** Fetch nutrition data for best match
4. **Calculate:** Scale nutrition values for 150g
5. **Return:** Calories, protein, carbs, fats

## API Features

### Search Foods

```python
from src.services.usda_service import usda_service

# Search for foods
results = usda_service.search_foods("apple", page_size=5)

for food in results:
    print(f"{food['description']} (ID: {food['fdcId']})")
```

### Get Nutrition

```python
# Get nutrition for a specific food
nutrition_data = usda_service.search_and_get_nutrition("banana")

print(f"Calories per 100g: {nutrition_data['nutrition_per_100g']['calories']}")
```

### Calculate for Quantity

```python
# Get nutrition for specific quantity
result = usda_service.get_nutrition_for_quantity("chicken breast", 150, "g")

print(f"150g chicken breast: {result['nutrition']['calories']} calories")
```

## Fallback System

The bot includes a **fallback database** for:

1. **Common Indian foods** (dosa, idli, roti, etc.) that may not be in USDA database
2. **API failures** (network issues, rate limits)
3. **Quick lookups** for very common items

### Fallback Foods

The following foods have local fallback data:
- Indian foods: dosa, idli, roti, chapati, dal, paratha, upma, samosa, paneer
- Common items: egg, rice, milk, banana, apple, bread, butter, ghee

### Priority Order

1. **USDA API** (primary source)
2. **Fallback database** (if API fails or food not found)
3. **Default values** (if both fail)

## Supported Units

The system supports various units and converts them automatically:

- **Weight:** g, grams, oz, lb
- **Volume:** ml, cup, tbsp, tsp
- **Count:** piece, pieces, serving

### Unit Conversions

```python
# Approximate conversions used:
1 oz = 28.35g
1 lb = 453.592g
1 cup = 240g (for liquids)
1 tbsp = 15g
1 tsp = 5g
```

## Rate Limits

USDA API rate limits (as of 2024):

- **1,000 requests per hour** per API key
- **No daily limit**
- Rate limit resets every hour

### Best Practices

1. **Cache results** when possible
2. **Use fallback database** for common items
3. **Batch requests** if processing multiple foods
4. **Handle errors gracefully** with fallback

## Error Handling

The integration includes robust error handling:

```python
try:
    nutrition = usda_service.search_and_get_nutrition("chicken")
except Exception as e:
    logger.error(f"USDA API error: {e}")
    # Falls back to local database automatically
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `USDA_API_KEY not configured` | Missing API key | Add key to `.env` |
| `No results found` | Food not in database | Use fallback or try different search term |
| `Rate limit exceeded` | Too many requests | Wait for rate limit reset (1 hour) |
| `Network error` | Internet connection | Check connection, use fallback |

## Configuration

All USDA API settings are in `config.py`:

```python
# USDA FoodData Central API
USDA_API_KEY: str = os.getenv("USDA_API_KEY", "")
USDA_API_URL: str = os.getenv(
    "USDA_API_URL",
    "https://api.nal.usda.gov/fdc/v1"
)
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USDA_API_KEY` | Yes | - | Your USDA API key |
| `USDA_API_URL` | No | `https://api.nal.usda.gov/fdc/v1` | API base URL |

## Testing

### Manual Testing

```bash
# Test the integration
python test_usda_integration.py

# Test with the bot (requires Telegram bot token)
python run_bot.py
```

### Test Cases

The test script (`test_usda_integration.py`) verifies:

1. ✅ API key configuration
2. ✅ Food search functionality
3. ✅ Nutrition data retrieval
4. ✅ Quantity calculations
5. ✅ FoodService integration

## Deployment

### Local Development

```bash
# 1. Set up environment
cp .env.example .env
# Add your USDA_API_KEY to .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test
python test_usda_integration.py

# 4. Run bot
python run_bot.py
```

### IBM Cloud / Code Engine

Add the USDA API key as a secret:

```bash
# Create secret
ibmcloud ce secret create --name usda-api-secret \
  --from-literal USDA_API_KEY=your_api_key_here

# Update application to use secret
ibmcloud ce application update calorie-tracker-bot \
  --env-from-secret usda-api-secret
```

Or add via IBM Cloud Console:
1. Go to Code Engine → Applications → calorie-tracker-bot
2. Click "Environment variables"
3. Add `USDA_API_KEY` with your key
4. Save and redeploy

## API Documentation

Full USDA FoodData Central API documentation:
- **API Guide:** https://fdc.nal.usda.gov/api-guide.html
- **API Spec:** https://fdc.nal.usda.gov/api-spec/fdc_api.html
- **Data Types:** https://fdc.nal.usda.gov/data-documentation.html

### Data Types in USDA Database

1. **Foundation Foods** - Core foods with detailed nutrient data
2. **SR Legacy** - Standard Reference Legacy database
3. **Survey (FNDDS)** - Food and Nutrient Database for Dietary Studies
4. **Branded Foods** - Commercial food products

## Troubleshooting

### Issue: "USDA_API_KEY is not configured"

**Solution:**
```bash
# Check if .env file exists
ls -la .env

# If not, create it
cp .env.example .env

# Add your API key
echo "USDA_API_KEY=your_key_here" >> .env
```

### Issue: "No results found for: [food name]"

**Solutions:**
1. Try a more generic search term (e.g., "chicken" instead of "tandoori chicken")
2. Check spelling
3. The food will use fallback database values

### Issue: Rate limit exceeded

**Solutions:**
1. Wait 1 hour for rate limit reset
2. Use fallback database for common items
3. Consider caching results

### Issue: Network errors

**Solutions:**
1. Check internet connection
2. Verify API URL is correct
3. System will automatically use fallback database

## Future Enhancements

Potential improvements:

- [ ] **Caching:** Cache API responses to reduce requests
- [ ] **Batch processing:** Process multiple foods in one request
- [ ] **User preferences:** Remember user's common foods
- [ ] **Smart matching:** Better food name matching algorithm
- [ ] **Nutrition goals:** Track against daily goals
- [ ] **Meal planning:** Suggest meals based on nutrition targets

## Support

For issues or questions:

1. Check this documentation
2. Run `python test_usda_integration.py` to diagnose
3. Check logs for error messages
4. Verify API key is valid at https://fdc.nal.usda.gov/

## License

USDA FoodData Central data is in the public domain and free to use.

---

**Last Updated:** March 2026  
**USDA API Version:** v1  
**Bot Version:** 2.0 (with USDA integration)