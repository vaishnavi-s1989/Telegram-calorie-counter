# How to Get Your USDA API Key

## Quick Steps

### 1. Visit the Signup Page
Go to: **https://fdc.nal.usda.gov/api-key-signup.html**

### 2. Fill Out the Form
You'll need to provide:
- **First Name**
- **Last Name**
- **Email Address**
- **Organization** (can be "Personal" or "Individual")
- Agree to terms of service

### 3. Submit and Check Email
- Click "Submit"
- Check your email inbox
- You'll receive your API key **instantly** (within seconds)

### 4. Add to Your .env File

Once you receive the key, add it to your `.env` file:

```bash
# Open your .env file
nano .env

# Or use any text editor
code .env

# Add this line (replace with your actual key):
USDA_API_KEY=your_actual_api_key_here
```

### 5. Test the Integration

```bash
# Make sure you're in the project directory
cd "/Users/vaishnavi/Desktop/Whatsupp calorie counter"

# Activate virtual environment (if not already active)
source env/bin/activate

# Run the test
python test_usda_integration.py
```

## Expected Output After Adding Key

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
  2. Chicken breast, raw (FDC ID: 171116)
  3. Chicken, broiler, breast, skinless, boneless, meat, raw (FDC ID: 331960)

------------------------------------------------------------
Test 2: Getting nutrition details for first result
------------------------------------------------------------
✓ Nutrition per 100g:
  - Calories: 165.0 kcal
  - Protein: 31.0g
  - Carbs: 0.0g
  - Fats: 3.6g

... (more tests)

============================================================
✅ All tests passed! USDA API integration is working.
============================================================
```

## Troubleshooting

### Issue: "USDA_API_KEY is not configured"
**Solution:** Make sure you added the key to `.env` file, not `.env.example`

### Issue: "No results found"
**Solution:** 
1. Check your internet connection
2. Verify the API key is correct (no extra spaces)
3. Try the test again

### Issue: Email not received
**Solution:**
1. Check spam/junk folder
2. Wait a few minutes
3. Try signing up again with a different email

## API Key Details

- **Cost:** FREE
- **Rate Limit:** 1,000 requests per hour
- **Expiration:** Does not expire
- **Usage:** Personal and commercial use allowed

## Next Steps After Testing

Once the test passes:

1. **Run the bot:**
   ```bash
   python run_bot.py
   ```

2. **Try logging food:**
   - Open Telegram
   - Find your bot
   - Send: `/start`
   - Send: `2 eggs and 150g chicken breast`
   - The bot will now use USDA data for nutrition!

## Support

If you encounter any issues:
1. Check the USDA_API_INTEGRATION.md file
2. Verify your .env file has the correct format
3. Make sure there are no extra spaces or quotes around the API key

---

**Need Help?** The API key signup is instant and straightforward. If you have any issues, let me know!