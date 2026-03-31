#!/usr/bin/env python3
"""
calculate-monthly-stats.py
Aggregates the last 4 weekly snapshots from data/history/ into data/monthly-stats.json.
Each weekly snapshot is a JSON file matching data/history/week-YYYY-MM-DD.json.
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

HISTORY_DIR = Path("data/history")
OUTPUT_PATH = Path("data/monthly-stats.json")


def load_history_files():
    if not HISTORY_DIR.exists():
        return []
    files = sorted(HISTORY_DIR.glob("week-*.json"), reverse=True)
    return files[:4]  # Most recent 4 weeks


def safe_load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: could not load {path}: {e}")
        return None


def main():
    files = load_history_files()
    if not files:
        print("No history files found in data/history/. Run weekly plan generation first.")
        # Write empty stats so monthly report can still run
        stats = {
            "generated_at": str(date.today()),
            "weeks_analyzed": 0,
            "message": "No history available yet"
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(stats, f, indent=2)
        sys.exit(0)

    weeks = []
    total_cost = 0
    total_on_budget = 0
    recipe_ids = []
    cuisine_counts = {}
    nutrition_adherence = []

    for fpath in files:
        data = safe_load(fpath)
        if not data:
            continue
        weeks.append(data)

        # Cost data
        cost = data.get("cost_estimate", {})
        weekly_cost = cost.get("grand_total", 0)
        budget = cost.get("budget", 0)
        total_cost += weekly_cost
        if budget and weekly_cost <= budget * 1.05:
            total_on_budget += 1

        # Recipe variety
        selected = data.get("selected_recipes", [])
        for r in selected:
            rid = r.get("id", "")
            cuisine = r.get("cuisine", "unknown")
            recipe_ids.append(rid)
            cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1

        # Nutrition
        nutrition = data.get("nutrition_summary", {})
        if nutrition:
            calorie_adherence = nutrition.get("calorie_adherence_pct", 0)
            nutrition_adherence.append(calorie_adherence)

    # Compute aggregates
    n_weeks = len(weeks)
    avg_weekly_cost = round(total_cost / n_weeks, 2) if n_weeks else 0
    budget_adherence_pct = round((total_on_budget / n_weeks) * 100) if n_weeks else 0
    avg_nutrition_adherence = round(sum(nutrition_adherence) / len(nutrition_adherence)) if nutrition_adherence else 0

    # Recipe frequency
    from collections import Counter
    recipe_counter = Counter(recipe_ids)
    top_recipes = [{"recipe_id": rid, "times_selected": count}
                   for rid, count in recipe_counter.most_common(5)]

    stats = {
        "generated_at": str(date.today()),
        "weeks_analyzed": n_weeks,
        "period_start": str(files[-1].stem.replace("week-", "")) if files else None,
        "period_end": str(files[0].stem.replace("week-", "")) if files else None,
        "cost": {
            "total_month": round(total_cost, 2),
            "average_weekly": avg_weekly_cost,
            "budget_adherence_pct": budget_adherence_pct,
            "on_budget_weeks": total_on_budget,
            "over_budget_weeks": n_weeks - total_on_budget
        },
        "nutrition": {
            "average_calorie_adherence_pct": avg_nutrition_adherence,
            "weeks_with_nutrition_data": len(nutrition_adherence)
        },
        "variety": {
            "unique_recipes_used": len(set(recipe_ids)),
            "total_recipe_selections": len(recipe_ids),
            "cuisine_breakdown": cuisine_counts,
            "top_5_recipes": top_recipes
        }
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Monthly stats calculated from {n_weeks} weeks")
    print(f"  Average weekly cost: ${avg_weekly_cost}")
    print(f"  Budget adherence: {budget_adherence_pct}% of weeks on-budget")
    print(f"  Unique recipes used: {len(set(recipe_ids))}")
    print(f"  Cuisine breakdown: {cuisine_counts}")


if __name__ == "__main__":
    main()
