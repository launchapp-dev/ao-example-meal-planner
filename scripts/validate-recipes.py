#!/usr/bin/env python3
"""
validate-recipes.py
Validates config/recipe-database.yaml for required fields and allergen conflicts.
Reads config/household-profile.yaml for the household allergen list.
Exits 0 on success, 1 on validation failure.
"""

import sys
import yaml
import os

REQUIRED_RECIPE_FIELDS = [
    "id", "name", "cuisine", "tags", "servings",
    "prep_time_min", "cook_time_min", "total_time_min",
    "difficulty", "ingredients", "nutrition_per_serving"
]
REQUIRED_NUTRITION_FIELDS = ["calories", "protein_g", "carbs_g", "fat_g", "fiber_g"]

def load_yaml(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)

def main():
    errors = []
    warnings = []

    # Load files
    db = load_yaml("config/recipe-database.yaml")
    profile = load_yaml("config/household-profile.yaml")

    recipes = db.get("recipes", [])
    allergens = [a.lower() for a in profile.get("household", {}).get("allergens", [])]

    if not recipes:
        errors.append("No recipes found in recipe-database.yaml")

    seen_ids = set()
    for i, recipe in enumerate(recipes):
        prefix = f"Recipe[{i}] '{recipe.get('name', 'UNNAMED')}'"

        # Check required fields
        for field in REQUIRED_RECIPE_FIELDS:
            if field not in recipe:
                errors.append(f"{prefix}: missing required field '{field}'")

        # Check duplicate IDs
        rid = recipe.get("id")
        if rid:
            if rid in seen_ids:
                errors.append(f"{prefix}: duplicate id '{rid}'")
            seen_ids.add(rid)

        # Check nutrition fields
        nutrition = recipe.get("nutrition_per_serving", {})
        for nf in REQUIRED_NUTRITION_FIELDS:
            if nf not in nutrition:
                errors.append(f"{prefix}: missing nutrition field '{nf}'")

        # Check allergen conflicts
        ingredients = recipe.get("ingredients", [])
        for ing in ingredients:
            ing_name = str(ing.get("name", "")).lower().replace("_", " ")
            for allergen in allergens:
                if allergen in ing_name:
                    errors.append(
                        f"{prefix}: ALLERGEN CONFLICT — ingredient '{ing_name}' matches household allergen '{allergen}'"
                    )

        # Check reasonable values
        servings = recipe.get("servings", 0)
        if servings < 1 or servings > 20:
            warnings.append(f"{prefix}: unusual servings value ({servings})")

        total_time = recipe.get("total_time_min", 0)
        if total_time <= 0:
            errors.append(f"{prefix}: total_time_min must be > 0")

    # Report
    print(f"Validated {len(recipes)} recipes against {len(allergens)} allergens")
    print(f"Household allergens: {', '.join(allergens) if allergens else 'none'}")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
        print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print(f"✓ All {len(recipes)} recipes are valid and allergen-safe")
        sys.exit(0)

if __name__ == "__main__":
    main()
