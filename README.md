# Meal Planning & Grocery Pipeline

An autonomous meal planning system that takes your household's dietary preferences and constraints, selects nutritionally-balanced recipes, builds a 7-day meal calendar, consolidates a cost-optimized grocery list, and produces a batch-cooking prep schedule — all running on a weekly schedule without manual intervention.

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                    WEEKLY PLAN WORKFLOW                       │
│                   (Every Sunday 8:00 AM)                     │
└──────────────────────────────────────────────────────────────┘

  [log-pantry]           Update pantry inventory, flag expiring items
       │
       ▼
  [select-recipes]       Opus — multi-constraint recipe optimization
  (recipe-curator)       • Dietary restrictions + allergens (hard block)
                         • Variety vs. last 4 weeks
                         • Pantry-first (use expiring items)
                         • Weekly budget fit
                         • Nutritional targets
       │
       ▼
  [review-nutrition]     Sonnet — validate weekly macro/calorie totals
  (dietary-analyst)
       │
       ├─ swap-needed ──→ [select-recipes] (retry, max 2 attempts)
       │
       ▼ approve
  [schedule-meals]       Sonnet — 7-day calendar with prep complexity routing
  (meal-scheduler)       • Quick meals Mon–Thu (<30 min)
                         • Longer meals Fri–Sun
                         • Leftover utilization mid-week
       │
       ▼
  [consolidate-grocery]  Haiku — ingredient consolidation + pantry subtraction
  (grocery-optimizer)
       │
       ▼
  [check-budget]         Haiku — compare estimate vs. weekly budget
  (grocery-optimizer)
       │
       ├─ over-budget ──→ [select-recipes] (substitute expensive items, max 2)
       ├─ adjust ───────→ [schedule-meals] (minor optimizations)
       │
       ▼ on-track
  [optimize-prep]        Sonnet — Sunday batch session + daily prep tasks
  (prep-planner)
       │
       ▼
  [compile-weekly-plan]  Haiku — generate plans/week-YYYY-MM-DD.md
  (report-compiler)           + shopping-lists/week-YYYY-MM-DD.md


┌──────────────────────────────────────────────────────────────┐
│                   MONTHLY REVIEW WORKFLOW                     │
│                (1st of each month, 9:00 AM)                  │
└──────────────────────────────────────────────────────────────┘

  [calculate-monthly-stats]  Aggregate 4 weeks of history
       │
       ▼
  [evaluate-month]           Sonnet — trend analysis + decision
  (dietary-analyst)
       │
       ├─ maintain ─────────→ [compile-monthly-report]
       ├─ adjust-targets ───→ [compile-monthly-report] (with updates)
       └─ expand-recipes ───→ [compile-monthly-report] (with suggestions)
```

---

## Quick Start

```bash
# 1. Clone and configure your household
cd examples/meal-planner
cp config/household-profile.yaml config/household-profile.yaml.bak
# Edit config/household-profile.yaml with your household's details

# 2. Start the daemon
ao daemon start --autonomous

# 3. Run onboarding (first-time setup)
ao queue enqueue \
  --title "meal-planner-onboard" \
  --description "Initial household onboarding and first week plan" \
  --workflow-ref onboard

# 4. Weekly plans will auto-generate every Sunday at 8:00 AM
# You can also trigger manually:
ao workflow run weekly-plan

# 5. Watch it work
ao daemon stream --pretty
```

---

## Agents

| Agent | Model | Role |
|---|---|---|
| **dietary-analyst** | claude-sonnet-4-6 | Analyzes dietary restrictions, calculates macro targets, validates nutritional adequacy, conducts monthly trend reviews |
| **recipe-curator** | claude-opus-4-6 | Multi-constraint recipe selection (nutrition × budget × variety × pantry-first); hardest optimization in the pipeline |
| **meal-scheduler** | claude-sonnet-4-6 | Arranges recipes into 7-day calendar considering weeknight time constraints and leftover utilization |
| **grocery-optimizer** | claude-haiku-4-5 | Consolidates ingredients, subtracts pantry inventory, estimates costs by aisle, budget gating |
| **prep-planner** | claude-sonnet-4-6 | Designs Sunday batch cooking session and daily prep tasks to minimize weeknight active cooking time |
| **report-compiler** | claude-haiku-4-5 | Generates the complete weekly plan document, printable shopping list, and monthly reports |

---

## AO Features Demonstrated

| Feature | Where Used |
|---|---|
| **Scheduled workflows** | Weekly plan every Sunday 8am; Monthly review 1st of month |
| **Decision contracts** | `review-nutrition` (approve/swap-needed), `check-budget` (on-track/over-budget/adjust), `evaluate-month` (maintain/adjust-targets/expand-recipes) |
| **Rework loops** | Budget exceeded → retry recipe selection (max 2); Nutrition miss → retry selection (max 2) |
| **Multi-agent pipeline** | 6 specialized agents with clear handoffs and distinct model choices |
| **Command phases** | `log-pantry` (Python script), `validate-recipe-database`, `calculate-monthly-stats` |
| **Multi-model routing** | Opus for complex optimization, Sonnet for analysis, Haiku for structured tasks |
| **Output contracts** | Each agent writes structured JSON (dietary-profile, selected-recipes, weekly-calendar, grocery-list, prep-schedule) |
| **Phase routing** | `adjust` verdict on budget check routes back to scheduling (not full recipe re-selection) |

---

## Requirements

### API Keys
- `ANTHROPIC_API_KEY` — for all Claude agents

### System Requirements
- Node.js 18+ (for MCP servers)
- Python 3.9+ (for validation and calculation scripts)
- AO daemon

### MCP Servers (auto-installed via npx)
- `@modelcontextprotocol/server-filesystem` — file read/write
- `@modelcontextprotocol/server-sequential-thinking` — multi-constraint reasoning for recipe-curator and prep-planner

---

## Configuration

### Household Profile (`config/household-profile.yaml`)
Set your household members, allergens, dietary restrictions, cuisine preferences, and weekly budget.

```yaml
household:
  allergens: [tree nuts, peanuts]       # Hard block — no recipes with these
  dietary_restrictions: [vegetarian]    # Recipe filter
  weekly_grocery_budget_usd: 150        # Budget gate triggers rework if exceeded
```

### Recipe Database (`config/recipe-database.yaml`)
45 pre-loaded recipes across 5 cuisines (Mediterranean, Indian, Mexican, Asian, American).
All are nut-free and vegetarian. Add your own following the same schema.

### Store Prices (`config/store-prices.yaml`)
Average grocery prices used for cost estimation. Update to match your local store.

### Pantry Inventory (`data/pantry-inventory.json`)
Current pantry contents. The `log-pantry` phase updates this at the start of each weekly run, removing expired items and flagging items expiring within 5 days for priority use.

---

## Output Files

| File | Contents |
|---|---|
| `plans/week-YYYY-MM-DD.md` | Full weekly plan: calendar, recipes, nutrition summary, prep schedule, grocery list |
| `shopping-lists/week-YYYY-MM-DD.md` | Standalone printable grocery list by aisle |
| `reports/month-YYYY-MM.md` | Monthly performance review: cost trends, nutrition adherence, top recipes |
| `data/weekly-calendar.json` | Structured 7-day meal schedule |
| `data/grocery-list.json` | Consolidated ingredient list by aisle |
| `data/cost-estimate.json` | Per-meal and total cost breakdown |
| `data/prep-schedule.json` | Sunday batch session + daily prep tasks |

---

## Example Weekly Plan Output

```
# Week of 2026-03-30 — The Sample Family
Total estimated cost: $134.50 / $150.00 budget (10.3% under)
Nutrition: ✓ On target (calories 98%, protein 104%, carbs 96%, fat 102%)

## 7-Day Meal Calendar

| Day       | Breakfast                 | Lunch                      | Dinner                          |
|-----------|---------------------------|----------------------------|---------------------------------|
| Monday    | Greek Yogurt Parfait      | Lentil Soup (leftover)     | Dal Tadka + Rice                |
| Tuesday   | Oatmeal with Honey        | Chana Masala (leftover)    | Black Bean Tacos                |
| Wednesday | Scrambled Eggs            | Fajita Bowl (leftover)     | Thai Coconut Curry + Rice       |
| Thursday  | Greek Yogurt Parfait      | Minestrone (leftover)      | Vegetable Fried Rice            |
| Friday    | Potato Hash               | Bibimbap Bowl              | Shakshuka with Bread            |
| Saturday  | Oatmeal with Honey        | Caprese Quinoa Salad       | Vegetable Biryani               |
| Sunday    | Scrambled Eggs            | Aloo Gobi + Dal (leftover) | Roasted Eggplant & Chickpea Stew|

## Sunday Batch Session (2h 15min)
- [ ] Cook 4 cups white rice (serves Mon, Wed, Thu, Sat)
- [ ] Simmer lentil soup × 8 servings (Mon lunch + Tue lunch)
- [ ] Make chana masala × 4 (Tue dinner + Wed lunch)
...
```
