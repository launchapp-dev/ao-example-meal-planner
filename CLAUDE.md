# Meal Planner — Agent Context

## What This Project Is

An autonomous weekly meal planning pipeline. Given a household's dietary constraints and preferences, it selects recipes, builds a 7-day meal calendar, generates a cost-optimized grocery list, and produces a batch-cooking prep schedule.

Runs fully on autopilot via AO daemon. No human intervention required after initial configuration.

---

## Data Flow

```
config/household-profile.yaml  ──→  dietary-analyst  ──→  data/dietary-profile.json
config/recipe-database.yaml    ──→  recipe-curator   ──→  data/selected-recipes.json
data/pantry-inventory.json     ──→  meal-scheduler   ──→  data/weekly-calendar.json
config/store-prices.yaml       ──→  grocery-optimizer ──→  data/grocery-list.json
                                                          data/cost-estimate.json
                                    prep-planner     ──→  data/prep-schedule.json
                                    report-compiler  ──→  plans/week-YYYY-MM-DD.md
                                                          shopping-lists/week-YYYY-MM-DD.md
```

## Key Constraints

1. **Allergens are hard constraints** — Never select a recipe containing tree nuts or peanuts. This is non-negotiable regardless of other optimization goals.

2. **Dietary restrictions are hard constraints** — All selected recipes must be vegetarian (no meat, poultry, or seafood).

3. **Budget gate with rework** — If estimated grocery cost exceeds budget by >5%, the workflow loops back to recipe selection with instructions to substitute expensive items. Maximum 2 retry attempts.

4. **Nutrition gate** — dietary-analyst validates that the selected recipe set meets weekly macro targets (±10% tolerance) before scheduling proceeds. If targets are missed, recipe selection retries.

5. **Pantry-first selection** — recipe-curator must prioritize recipes using pantry items flagged with "USE_SOON" or "priority". Reduce food waste.

---

## File Formats

### data/dietary-profile.json
```json
{
  "restriction_list": ["vegetarian"],
  "allergen_flags": ["tree nuts", "peanuts"],
  "preference_weights": { "Mediterranean": 0.9, "Indian": 0.85 },
  "calorie_target_per_week": 38500,
  "macro_targets": {
    "protein_g_per_week": 420,
    "carbs_g_per_week": 1470,
    "fat_g_per_week": 490,
    "fiber_g_per_week": 175
  }
}
```

### data/selected-recipes.json
```json
[
  {
    "id": "ind-001",
    "name": "Dal Tadka",
    "cuisine": "Indian",
    "servings_needed": 4,
    "nutritional_contribution": { "calories": 1160, "protein_g": 68 },
    "pantry_items_used": ["lentils_red", "cumin_ground"],
    "estimated_cost": 4.50,
    "selection_reason": "High protein, uses pantry lentils nearing expiry, fits Indian preference weight"
  }
]
```

### data/weekly-calendar.json
```json
{
  "week_start": "2026-03-30",
  "days": [
    {
      "day": "Monday",
      "date": "2026-03-30",
      "meals": {
        "breakfast": { "recipe_id": "ame-006", "servings": 3, "is_leftover": false },
        "lunch": { "recipe_id": "med-005", "servings": 4, "is_leftover": true },
        "dinner": { "recipe_id": "ind-001", "servings": 4, "is_leftover": false },
        "snack": null
      }
    }
  ],
  "leftover_plan": {
    "med-005": { "cooked_day": "Sunday", "consumed_days": ["Monday", "Tuesday"] }
  }
}
```

### data/grocery-list.json
```json
{
  "generated_at": "2026-03-30",
  "week_start": "2026-03-30",
  "by_aisle": {
    "produce": [
      { "name": "spinach", "quantity": 2, "unit": "bag", "estimated_cost": 6.98, "pantry_available": "1 bag", "notes": "1 bag already in pantry" }
    ],
    "pantry": [],
    "dairy": []
  }
}
```

---

## Agents and Their Files

| Agent | Reads | Writes |
|---|---|---|
| dietary-analyst | household-profile.yaml | data/dietary-profile.json, config/nutrition-targets.yaml |
| recipe-curator | recipe-database.yaml, dietary-profile.json, pantry-inventory.json, history/ | data/selected-recipes.json |
| meal-scheduler | selected-recipes.json, household-profile.yaml | data/weekly-calendar.json |
| grocery-optimizer | weekly-calendar.json, recipe-database.yaml, pantry-inventory.json, store-prices.yaml | data/grocery-list.json, data/cost-estimate.json, shopping-lists/ |
| prep-planner | weekly-calendar.json, recipe-database.yaml | data/prep-schedule.json |
| report-compiler | all data/ files, recipe-database.yaml | plans/, reports/ |

---

## Workflow Routing Notes

The `check-budget` phase has three verdicts:
- `on-track` → advance to optimize-prep
- `over-budget` → loop back to select-recipes (recipe-curator substitutes expensive items)
- `adjust` → loop back to schedule-meals (meal-scheduler swaps a couple specific meals)

The `review-nutrition` phase:
- `approve` → advance to schedule-meals
- `swap-needed` → loop back to select-recipes (recipe-curator fixes the specific nutrient gap)

Both loops have `max_rework_attempts: 2`. After 2 failed attempts, the workflow fails and logs the constraint conflict for human review.

---

## Running Scripts Manually

```bash
# Validate recipe database for errors and allergen conflicts
python3 scripts/validate-recipes.py

# Update pantry inventory (removes expired, flags near-expiry)
python3 scripts/log-pantry.py

# Aggregate last 4 weeks into monthly stats
python3 scripts/calculate-monthly-stats.py
```

---

## Adding New Recipes

Add entries to `config/recipe-database.yaml` following the existing schema. Required fields:
- id (unique, format: cuisine-prefix + number e.g. "ind-006")
- name, cuisine, tags, servings, prep_time_min, cook_time_min, total_time_min, difficulty
- ingredients (list with name, quantity, unit matching store-prices.yaml keys)
- nutrition_per_serving (calories, protein_g, carbs_g, fat_g, fiber_g)

Run `python3 scripts/validate-recipes.py` after adding recipes to verify correctness.
