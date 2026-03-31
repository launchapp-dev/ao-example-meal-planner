# Meal Planner — Build Plan

## Overview

A meal planning pipeline that takes a household's dietary preferences and constraints, selects recipes to meet nutritional targets, builds a weekly meal calendar, consolidates grocery lists with cost estimates, and produces optimized prep schedules with batch cooking strategies.

---

## Agents

| Agent | Model | Role |
|---|---|---|
| **dietary-analyst** | claude-sonnet-4-6 | Analyzes household dietary preferences, restrictions, allergies, and nutritional targets. Produces the dietary profile used for recipe selection. |
| **recipe-curator** | claude-opus-4-6 | Selects recipes from the recipe database that match dietary constraints, nutritional targets, variety goals, and budget. Uses sequential-thinking for complex multi-constraint optimization. |
| **meal-scheduler** | claude-sonnet-4-6 | Arranges selected recipes into a 7-day meal calendar balancing variety, prep complexity, and leftover utilization. |
| **grocery-optimizer** | claude-haiku-4-5 | Consolidates ingredients across all meals, merges quantities, estimates costs per item and total, flags pantry items already available. |
| **prep-planner** | claude-sonnet-4-6 | Creates the weekly prep schedule — batch cooking windows, mise en place order, storage instructions, reheat notes. Optimizes for minimal active cooking time. |
| **report-compiler** | claude-haiku-4-5 | Generates the final weekly meal plan document: calendar view, grocery list, cost summary, prep schedule, and nutritional summary. |

## MCP Servers

| Server | Purpose |
|---|---|
| `filesystem` | Read/write all config, data, and output files |
| `sequential-thinking` | Complex recipe selection reasoning and prep optimization |

---

## Data Model

| File | What It Contains | Who Reads | Who Writes |
|---|---|---|---|
| `config/household-profile.yaml` | Members, dietary restrictions, allergies, cuisine preferences, disliked ingredients, meal count/day, budget | dietary-analyst, recipe-curator | Never modified after onboarding |
| `config/recipe-database.yaml` | ~50 recipes: name, cuisine, ingredients (with quantities), prep time, cook time, servings, calories, macros, tags, difficulty | recipe-curator, grocery-optimizer | Static reference (can be expanded) |
| `config/nutrition-targets.yaml` | Daily calorie/macro targets per household member, micronutrient goals | dietary-analyst, recipe-curator | dietary-analyst (create during onboard) |
| `config/store-prices.yaml` | Common ingredient prices per unit (estimated averages) | grocery-optimizer | Static reference |
| `data/dietary-profile.json` | Analyzed dietary constraints, allergen flags, preference weights | recipe-curator, meal-scheduler | dietary-analyst |
| `data/pantry-inventory.json` | Current pantry contents with quantities and expiry estimates | grocery-optimizer, recipe-curator | log-pantry.sh (update), grocery-optimizer (deplete after shopping) |
| `data/selected-recipes.json` | This week's chosen recipes with nutritional fit scores | meal-scheduler, grocery-optimizer, prep-planner | recipe-curator |
| `data/weekly-calendar.json` | 7-day meal schedule (breakfast, lunch, dinner, snacks) with recipe assignments | grocery-optimizer, prep-planner, report-compiler | meal-scheduler |
| `data/grocery-list.json` | Consolidated ingredient list with quantities, estimated costs, aisle grouping | prep-planner, report-compiler | grocery-optimizer |
| `data/cost-estimate.json` | Per-meal and total weekly cost breakdown, budget comparison | report-compiler | grocery-optimizer |
| `data/prep-schedule.json` | Ordered prep tasks with timing, batch cooking groups, storage instructions | report-compiler | prep-planner |
| `data/history/` | Past weekly plans, grocery lists, cost actuals for trend analysis | recipe-curator (variety), report-compiler | calculate-weekly-stats.sh |
| `plans/` | Final weekly plan documents (markdown) | Household reference | report-compiler |
| `shopping-lists/` | Printable grocery lists (markdown) | Household reference | grocery-optimizer |

---

## Phases

### Onboard Household (one-time)

| Phase | Mode | Agent | What It Does |
|---|---|---|---|
| `analyze-dietary-needs` | agent | dietary-analyst | Reads household-profile.yaml, analyzes dietary restrictions/allergies/preferences, calculates per-member nutritional targets, writes dietary-profile.json and nutrition-targets.yaml |
| `validate-recipe-database` | command | — | Runs script to validate recipe-database.yaml: checks all recipes have required fields, flags allergen conflicts with household profile |
| `build-initial-plan` | agent | recipe-curator | Selects first week's recipes matching dietary profile, writes selected-recipes.json |
| `schedule-first-week` | agent | meal-scheduler | Creates 7-day calendar from selected recipes, writes weekly-calendar.json |
| `generate-first-grocery-list` | agent | grocery-optimizer | Consolidates ingredients, estimates costs, writes grocery-list.json, cost-estimate.json, and shopping-lists/week-1.md |
| `plan-first-prep` | agent | prep-planner | Creates prep schedule for week 1, writes prep-schedule.json |
| `compile-first-plan` | agent | report-compiler | Generates the complete week 1 plan document to plans/week-1.md |

### Weekly Plan Generation (scheduled weekly)

| Phase | Mode | Agent | What It Does |
|---|---|---|---|
| `log-pantry` | command | — | Runs pantry update script (user edits pantry-inventory.json or script prompts) |
| `select-recipes` | agent | recipe-curator | Selects recipes for the week considering: dietary profile, variety vs recent history, pantry items to use up (expiring soon), seasonal availability, budget. Uses sequential-thinking. |
| `review-nutrition` | agent | dietary-analyst | Validates selected recipes meet weekly nutritional targets. Decision: approve / swap-needed |
| `schedule-meals` | agent | meal-scheduler | Arranges approved recipes into 7-day calendar, balancing prep complexity across days, utilizing leftovers, grouping similar cuisines |
| `consolidate-grocery` | agent | grocery-optimizer | Merges ingredients, subtracts pantry inventory, estimates costs per item, groups by store aisle |
| `check-budget` | agent | grocery-optimizer | Compares estimated total vs weekly budget. Decision: on-track / over-budget / adjust |
| `optimize-prep` | agent | prep-planner | Creates prep schedule: batch cooking Sunday, daily prep tasks, storage/reheat instructions |
| `compile-weekly-plan` | agent | report-compiler | Generates final plan document with calendar, grocery list, cost summary, prep schedule |

### Monthly Review (scheduled monthly)

| Phase | Mode | Agent | What It Does |
|---|---|---|---|
| `calculate-monthly-stats` | command | — | Aggregates 4 weeks of data: average cost, nutrition adherence, recipe variety stats |
| `evaluate-month` | agent | dietary-analyst | Reviews nutrition trends, cost trends, identifies patterns (over-budget weeks, missed targets). Decision: maintain / adjust-targets / expand-recipes |
| `compile-monthly-report` | agent | report-compiler | Generates monthly summary: cost trend, nutrition adherence, favorite meals, recommendations |

---

## Workflow Routing

### weekly-plan
```
log-pantry → select-recipes → review-nutrition
  ├─ approve → schedule-meals → consolidate-grocery → check-budget
  │    ├─ on-track → optimize-prep → compile-weekly-plan
  │    ├─ over-budget → select-recipes (rework, max 2 attempts)
  │    └─ adjust → schedule-meals (swap expensive items, continue)
  └─ swap-needed → select-recipes (rework, max 2 attempts)
```

### monthly-review
```
calculate-monthly-stats → evaluate-month
  ├─ maintain → compile-monthly-report
  ├─ adjust-targets → compile-monthly-report (with updated targets)
  └─ expand-recipes → compile-monthly-report (with recipe suggestions)
```

---

## Scripts

| Script | Purpose |
|---|---|
| `scripts/validate-recipes.sh` | Validates recipe-database.yaml structure, checks allergen conflicts |
| `scripts/log-pantry.sh` | Updates pantry-inventory.json (reads current, applies changes) |
| `scripts/calculate-weekly-stats.sh` | Calculates weekly nutrition adherence, cost actuals, archives to history/ |
| `scripts/calculate-monthly-stats.sh` | Aggregates monthly data from history/ |

All scripts use Python3 embedded via heredoc (standard library only, no external packages).

---

## Supporting Files to Create

### Config Files
- `config/household-profile.yaml` — Sample household (2 adults, 1 child, vegetarian-friendly with nut allergy, $150/week budget)
- `config/recipe-database.yaml` — 40-50 recipes across cuisines (Mediterranean, Asian, Mexican, American, Indian) with full nutritional data
- `config/nutrition-targets.yaml` — Generated by dietary-analyst during onboarding
- `config/store-prices.yaml` — Average grocery prices for common ingredients

### Sample Data
- `data/pantry-inventory.json` — Starting pantry with common staples
- `data/history/` — Empty directory for weekly snapshots

### Output Directories
- `plans/` — Weekly plan documents
- `shopping-lists/` — Printable grocery lists

---

## Schedule Configuration

| Schedule | Cron | Workflow |
|---|---|---|
| Weekly plan generation | `0 8 * * 0` (Sunday 8am) | weekly-plan |
| Monthly review | `0 9 1 * *` (1st of month 9am) | monthly-review |

---

## Key Design Decisions

1. **Recipe-curator uses Opus** — Recipe selection is the hardest optimization problem (balance nutrition, variety, budget, preferences, pantry usage, prep complexity). Worth the stronger model.
2. **Budget check as rework loop** — If estimated grocery cost exceeds budget, loop back to recipe selection with a budget constraint flag. Max 2 rework attempts before accepting.
3. **Nutrition review as gate** — Dietary-analyst validates the recipe set meets weekly macro/calorie targets before scheduling. Prevents a week of nutritionally unbalanced meals.
4. **Pantry-first recipe selection** — Recipe-curator prioritizes recipes that use ingredients already in the pantry, especially items nearing expiry. Reduces waste and cost.
5. **Batch cooking optimization** — Prep-planner identifies recipes with shared base components (e.g., rice, roasted vegetables, marinades) and groups them into batch cooking windows.
6. **Haiku for cost/reporting** — Grocery optimization and reporting are structured, lower-complexity tasks. Haiku handles these efficiently.

---

## README Outline

1. What This Project Does (2-3 sentences)
2. How It Works (agent pipeline diagram)
3. Quick Start (ao daemon start, configure household)
4. Configuration (household profile, recipe database, budget)
5. Workflows (onboard, weekly plan, monthly review)
6. Output Examples (sample weekly plan, grocery list, prep schedule)
7. AO Features Demonstrated (schedules, decision contracts, rework loops, command phases, multi-agent)
