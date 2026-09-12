# StockPot AI - Flask Backend API

StockPot AI is a meal planning and smart grocery shopping backend for Sri Lankan households. It powers the StockPot AI mobile application built with Expo, React Native, and TypeScript.

---

## Features

- **Supabase Authentication & Profiles**: Secure sign-up, sign-in, token verification (`Authorization: Bearer <token>`), and customizable profile preferences.
- **Smart Recipe Catalog**: 10 authentic recipes with calories, prep time, protein levels, and ingredients.
- **Deterministic Serving Calculations**: Mathematically adjusts recipe ingredient quantities (`base_quantity * requested_servings / base_servings`) without AI hallucinations.
- **Weekly Meal Planner**: Schedule meals across the week with real-time budget tracking.
- **Smart Shopping List Generator**: Auto-generates aggregated shopping lists from meal plans, strictly combining duplicate ingredients across recipes.
- **Supermarket Price Comparison**: Compares total basket costs across **Cargills**, **Keells**, **Glomark**, and **Local Market**, checking live stock, calculating active discounts, Haversine distance from user GPS coordinates, identifying the cheapest store, and computing exact savings vs. the next-best store.
- **Active Discounts Engine**: Real-time percentage and fixed discounts for supermarket products in LKR.
- **Savings & Activity Tracking**: Tracks user savings, calculates monthly trends, and logs activity events.
- **Google Gemini AI Integration**:
  - AI recipe recommendation engine to rank existing database recipes.
  - Contextual AI chatbot grounded strictly in existing catalog and discount data.
- **Dual-Mode Data Architecture**: Runs seamlessly in standalone mock mode (`USE_MOCK_DATA=true`) or fully connected with Supabase PostgreSQL.

---

## Project Structure

```
stockpot-backend/
├── app/
│   ├── __init__.py               # Flask app factory, CORS, error handlers, /api/health
│   ├── config.py                 # Configuration loader from .env
│   ├── extensions.py             # Supabase client & Gemini API client
│   ├── routes/
│   │   ├── __init__.py           # Blueprint registrar
│   │   ├── auth_routes.py        # /api/auth (register, login, logout, me)
│   │   ├── user_routes.py        # /api/profile (GET, PATCH)
│   │   ├── recipe_routes.py      # /api/recipes (list, details, serving calc, suggestions)
│   │   ├── meal_plan_routes.py   # /api/meal-plans (current, items CRUD, summary)
│   │   ├── shopping_routes.py    # /api/shopping-lists (from meal plan, compare, discounts)
│   │   ├── store_routes.py       # /api/stores (list, details, discounts)
│   │   ├── savings_routes.py     # /api/savings (summary, trend, recent, add)
│   │   ├── activity_routes.py    # /api/activity (timeline filtered by type)
│   │   └── ai_routes.py          # /api/ai/chat (Gemini chatbot with context)
│   ├── services/
│   │   ├── auth_service.py       # Supabase auth & profile sync
│   │   ├── recipe_service.py     # Recipe queries & deterministic serving calculations
│   │   ├── meal_plan_service.py  # Weekly planning & budget math
│   │   ├── shopping_service.py   # Aggregation & deduplication of ingredients
│   │   ├── comparison_service.py # Supermarket price comparison & distance
│   │   ├── discount_service.py   # Discount calculation (percentage & fixed)
│   │   ├── savings_service.py    # Savings statistics & monthly trends
│   │   ├── activity_service.py   # Activity logging & feeds
│   │   └── ai_service.py         # Google Gemini recipe ranking & grounded chatbot
│   ├── utils/
│   │   ├── decorators.py         # @require_auth & @optional_auth middleware
│   │   ├── helpers.py            # Haversine distance & validators
│   │   └── response.py           # Standard JSON response formatters
│   └── mock_data/
│       ├── ingredients.py        # 25 ingredients with standard units
│       ├── recipes.py            # 10 detailed recipes
│       ├── stores.py             # 4 supermarket chains with GPS locations
│       ├── products.py           # 25+ grocery products
│       ├── prices.py             # Realistic store prices in LKR
│       └── discounts.py          # Active percentage & fixed discounts
├── scripts/
│   ├── schema.sql                # PostgreSQL DDL for Supabase
│   └── seed_database.py         # Idempotent database seeder
├── tests/
│   └── test_calculations.py      # Automated tests for serving math, comparison, distance
├── run.py                        # Entry point binding to 0.0.0.0:5000
├── requirements.txt              # Dependencies
├── .env.example                  # Environment variable template
└── README.md                     # Documentation
```

---

## Getting Started

### 1. Requirements

- Python 3.10+ (tested on Python 3.14)
- Node.js & Expo CLI (for the frontend)

### 2. Set Up Virtual Environment

Open PowerShell or Command Prompt in the backend directory:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Or Windows Command Prompt (cmd)
.venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Edit `.env` as needed:

```env
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# Supabase Credentials (Optional for mock development)
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi...

# Google Gemini API Key (Optional for mock development)
GEMINI_API_KEY=AIzaSy...

# Set to true to use realistic mock data when Supabase is empty or unconfigured
USE_MOCK_DATA=true

# CORS configuration
CORS_ORIGINS=*
```

---

## Supabase Setup (Optional)

If you have a Supabase project and want to use live PostgreSQL:

1. Log in to [Supabase Dashboard](https://supabase.com/dashboard).
2. Open the **SQL Editor** in your Supabase project.
3. Copy the contents of `scripts/schema.sql` and run the script. This creates all 14 tables, constraints, and indexes.
4. Copy your project URL, anon key, and service role key into `.env`.
5. Run the idempotent database seeder:

```bash
python scripts/seed_database.py
```

---

## Running the Backend

Start the development server:

```bash
python run.py
```

Output:
```
==================================================
 StockPot AI Backend Server Running
 Local URL:   http://localhost:5000
 Network URL: http://0.0.0.0:5000
 Health API:  http://localhost:5000/api/health
 Mock Mode:   True
==================================================
```

Verify the server is running:
- Open your browser or run: `curl http://localhost:5000/api/health`
- Response: `{"success": true, "data": {"service": "StockPot API", "status": "ok"}}`

---

## Connecting the Expo Mobile App

> [!IMPORTANT]
> **Do NOT use `http://localhost:5000` on a physical phone!**
> On a physical phone running Expo Go, `localhost` points to the phone itself, not your development PC.

### Step 1: Find Your Computer's LAN IP Address
Open PowerShell and run:
```powershell
ipconfig
```
Look for **IPv4 Address** under your Wi-Fi or Ethernet adapter (for example: `192.168.1.10`).

### Step 2: Configure Your Expo App
In your Expo frontend API config (e.g. `api/client.ts` or `.env` in the Expo project):

```typescript
// Replace 192.168.1.10 with your PC's actual IPv4 address
export const API_BASE_URL = "http://192.168.1.10:5000/api";
```

Ensure both your computer and your phone are connected to the same Wi-Fi network.

---

## Running Automated Tests

Run the test suite covering mathematical calculations, ingredient aggregation, and store comparison:

```bash
python -m unittest discover -s tests -v
```

---

## Complete API Reference

All endpoints return uniform JSON:

- **Success**: `{"success": true, "data": { ... }}`
- **Error**: `{"success": false, "error": {"message": "Readable error"}}`

### Authentication (`/api/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user & profile | No |
| `POST` | `/api/auth/login` | Login with email & password | No |
| `POST` | `/api/auth/logout` | Invalidate session | No |
| `GET` | `/api/auth/me` | Get authenticated user | Yes |

### User Profile (`/api/profile`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/profile` | Get current user profile | Yes |
| `PATCH` | `/api/profile` | Update profile preferences & budget | Yes |

### Recipes (`/api/recipes`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/recipes` | List recipes (`?category=...&search=...&limit=20&page=1`) | No |
| `GET` | `/api/recipes/<id>` | Get recipe details & ingredients | No |
| `GET` | `/api/recipes/<id>/ingredients?servings=N` | Calculate serving ingredient quantities | No |
| `POST` | `/api/recipes/suggestions` | Gemini AI-ranked recipe suggestions | No |

### Meal Plans (`/api/meal-plans`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/meal-plans/current` | Get active weekly meal plan | Yes |
| `POST` | `/api/meal-plans` | Create a new weekly meal plan | Yes |
| `POST` | `/api/meal-plans/<id>/items` | Add recipe meal to plan | Yes |
| `PATCH` | `/api/meal-plans/<id>/items/<item_id>` | Update meal item servings/schedule | Yes |
| `DELETE` | `/api/meal-plans/<id>/items/<item_id>` | Remove meal item | Yes |
| `GET` | `/api/meal-plans/<id>/summary` | Get budget & spending metrics | Yes |

### Shopping Lists & Comparison (`/api/shopping-lists`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/shopping-lists/from-meal-plan/<plan_id>` | Generate list (combines duplicate ingredients) | Yes |
| `GET` | `/api/shopping-lists/current` | Get user's active shopping list | Yes |
| `GET` | `/api/shopping-lists/<id>` | Get shopping list by ID | Yes |
| `PATCH` | `/api/shopping-lists/<id>/items/<item_id>` | Toggle item selection (`{"selected": false}`) | Yes |
| `GET` | `/api/shopping-lists/<id>/compare` | Compare store basket prices (`?latitude=...&longitude=...`) | No |
| `GET` | `/api/shopping-lists/<id>/discounts` | Get active discounts for list items | No |

### Supermarkets (`/api/stores`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/stores` | List all supermarket chains | No |
| `GET` | `/api/stores/<id>` | Get store details | No |
| `GET` | `/api/stores/<id>/discounts` | Get active discounts at this store | No |

### Savings (`/api/savings`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/savings/summary` | Cumulative savings, goal & averages | Yes |
| `GET` | `/api/savings/trend` | Monthly savings history trend | Yes |
| `GET` | `/api/savings/recent` | Recent savings events | Yes |
| `POST` | `/api/savings` | Record verified savings event | Yes |

### Activity History (`/api/activity`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/activity` | Activity feed (`?type=all\|purchases\|meal_plans\|savings`) | Yes |

### AI Assistant (`/api/ai`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/ai/chat` | AI chatbot for meal planning & grocery questions | Optional |

---

## Mock vs. Production Components

| Component | Current State | How to Replace with Live Data |
|---|---|---|
| **Recipe Catalog** | 10 realistic recipes in `mock_data/recipes.py` | Insert recipes into Supabase `recipes` table or connect an external recipe API. |
| **Supermarket Stores** | Cargills, Keells, Glomark, Local Market | Populate Supabase `stores` table with store branches and coordinates. |
| **Supermarket Prices** | Mock prices in `mock_data/prices.py` | Sync via official supermarket scraper scripts or supermarket partner APIs into `store_prices` table. |
| **Discounts** | 8 active discounts in `mock_data/discounts.py` | Insert promotions into Supabase `discounts` table. |
| **Price Comparison Math** | Production-ready Python calculation | **Keep as-is**: Already uses exact basket aggregation and Haversine distance. |
| **Serving Calculations** | Production-ready Python calculation | **Keep as-is**: Deterministic formula (`base_qty * servings / base_servings`). |
| **Gemini Recipe Ranking** | Production-ready | Supply `GEMINI_API_KEY` in `.env` to enable live Gemini AI ranking. |
