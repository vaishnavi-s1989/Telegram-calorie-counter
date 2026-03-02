# Telegram-Based Calorie & Macro Tracking App - Design Documentation

## 1. Product Vision

Build a Telegram-based calorie tracking assistant that:

- Accepts food input via text (e.g., "2 eggs and 1 dosa")
- Calculates calories and macronutrients (protein, carbs, fats)
- Stores daily history
- Generates progress summaries and graphs on demand
- Feels lightweight and conversational

### Target Persona

- Busy professionals
- People who prefer chat-based interfaces
- Users who do not want to install another mobile app

---

## 2. Core User Experience (Telegram Interface)

### 2.1 Primary Commands

#### `/start`
Initializes user and explains usage.

#### `/log`
**Example:**
```
/log 2 eggs and 1 dosa
```

**Response:**
- Calories
- Protein
- Carbs
- Fats
- Running daily total

#### `/today`
Shows total calories and macros for the day.

#### `/history`
Shows last 7 days summary.

#### `/graph`
Returns a calorie trend graph image.

#### `/reset`
Clears today's entries (with confirmation).

---

## 3. Functional Architecture

### 3.1 High-Level Flow

```
User (Telegram)
    ↓
Telegram Bot API (Webhook)
    ↓
FastAPI Backend (IBM Code Engine)
    ↓
Food Parsing + Nutrition Lookup
    ↓
Database Storage
    ↓
Response Sent Back to Telegram
```

---

## 4. Core Components

### 4.1 Telegram Bot Layer

- Created via BotFather
- Webhook pointing to IBM Code Engine URL
- Handles:
  - Commands
  - Text messages
  - User identification via Telegram user ID

### 4.2 Backend (FastAPI)

**Responsibilities:**
- Parse food text
- Extract quantities
- Normalize food names
- Fetch nutrition data
- Store entries
- Generate reports
- Create graphs (matplotlib)

### 4.3 Nutrition Data Source

**Options:**
- Open Food Facts API
- Static curated JSON (Indian food optimized)
- Hybrid (API + local overrides)

**Recommended:** Start with Open Food Facts + local fallback.

### 4.4 Database Design

#### Minimal Schema:

**Users**
- `telegram_user_id` (PK)
- `name`
- `created_at`

**FoodEntries**
- `id`
- `telegram_user_id`
- `date`
- `food_name`
- `quantity`
- `calories`
- `protein`
- `carbs`
- `fats`
- `timestamp`

**DailySummary** (optional optimization)
- `telegram_user_id`
- `date`
- `total_calories`
- `total_protein`
- `total_carbs`
- `total_fats`

#### Database Options:
- SQLite (MVP)
- PostgreSQL (Production)

---

## 5. Macro Calculation Logic

For each food item:

```
Total calories = quantity × calories_per_unit
Total protein = quantity × protein_per_unit
Total carbs = quantity × carbs_per_unit
Total fats = quantity × fats_per_unit
```

Aggregate per day.

---

## 6. Graph Generation

### Command: `/graph`

**Process:**
1. Fetch last 7–30 days data
2. Generate calorie trend line graph
3. Save as PNG
4. Send as Telegram photo message

### Graph Types (Phase 2):
- Calorie trend
- Protein intake trend
- Macro distribution pie chart

---

## 7. MVP Scope (Phase 1)

### Must Have:
- ✅ Text logging
- ✅ Daily totals
- ✅ 7-day calorie graph
- ✅ SQLite database
- ✅ Deployed on IBM Code Engine

### Nice to Have:
- Macro breakdown per meal
- Editable entries
- Delete specific entry

---

## 8. Future Enhancements (Phase 2+)

- Voice message support (speech-to-text)
- AI food parsing using watsonx
- Goal tracking (weight loss, muscle gain)
- Macro targets and alerts
- Weekly PDF report export
- Multi-language support

---

## 9. Non-Functional Considerations

### Scalability:
- Stateless FastAPI app
- Database connection pooling

### Security:
- Validate webhook origin
- Rate limit spam users

### Cost Control:
- Keep instance scale low
- Use lightweight DB initially

---

## 10. Technology Stack

### Backend:
- **Framework:** FastAPI
- **Language:** Python 3.9+
- **Deployment:** IBM Code Engine

### Database:
- **MVP:** SQLite
- **Production:** PostgreSQL

### APIs & Libraries:
- **Telegram Bot API:** python-telegram-bot
- **Nutrition Data:** Open Food Facts API
- **Graphing:** matplotlib
- **NLP/Parsing:** spaCy or regex-based parsing

### DevOps:
- **Container:** Docker
- **CI/CD:** GitHub Actions (optional)
- **Monitoring:** IBM Cloud Monitoring

---

## 11. Development Phases

### Phase 1: MVP (Weeks 1-2)
- Set up Telegram bot
- Implement basic commands (/start, /log, /today)
- Create SQLite database
- Deploy to IBM Code Engine
- Basic food parsing and nutrition lookup

### Phase 2: Enhanced Features (Weeks 3-4)
- Add /history and /graph commands
- Improve food parsing accuracy
- Add local Indian food database
- Implement data validation and error handling

### Phase 3: Polish & Scale (Weeks 5-6)
- Migrate to PostgreSQL
- Add user preferences
- Implement rate limiting
- Performance optimization
- User testing and feedback

---

## 12. API Endpoints (FastAPI)

### Webhook Endpoint:
```
POST /webhook
```
Receives updates from Telegram Bot API

### Health Check:
```
GET /health
```
Returns service status

### Internal Endpoints (if needed):
```
GET /api/user/{telegram_user_id}/entries
GET /api/user/{telegram_user_id}/summary
POST /api/user/{telegram_user_id}/entry
DELETE /api/user/{telegram_user_id}/entry/{entry_id}
```

---

## 13. Error Handling Strategy

- Invalid food input → Suggest corrections
- API failures → Use cached/local data
- Database errors → Retry with exponential backoff
- User errors → Friendly error messages with examples

---

## 14. Testing Strategy

### Unit Tests:
- Food parsing logic
- Macro calculations
- Database operations

### Integration Tests:
- Telegram webhook handling
- API integrations
- End-to-end command flows

### Manual Testing:
- User experience flows
- Edge cases
- Performance under load

---

## 15. Deployment Checklist

- [ ] Create Telegram bot via BotFather
- [ ] Set up IBM Code Engine project
- [ ] Configure environment variables
- [ ] Deploy FastAPI application
- [ ] Set up webhook URL
- [ ] Initialize database
- [ ] Test all commands
- [ ] Monitor logs and errors
- [ ] Set up backup strategy

---

## Document Version
- **Version:** 1.0
- **Last Updated:** 2026-02-27
- **Status:** Initial Design

