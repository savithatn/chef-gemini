#!/usr/bin/env python3
"""Seed script for Chef Gemini Firestore database."""

import sys
from google.cloud import firestore

# Hardcode the project ID as requested to ensure compatibility with Agent Platform
FIRESTORE_PROJECT = "qwiklabs-gcp-02-851ad8720399"

def seed_firestore():
    print(f"Connecting to Firestore for project: {FIRESTORE_PROJECT}...")
    db = firestore.Client(project=FIRESTORE_PROJECT)

    # 1. Seed Recipes
    recipes = [
        {
            "id": "spaghetti-carbonara",
            "title": "Spaghetti Carbonara",
            "cuisine": "Italian",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "ingredients": ["200g spaghetti", "100g guanciale or pancetta", "2 large eggs", "50g Pecorino Romano", "Black pepper"],
            "instructions": [
                "Boil spaghetti in salted water until al dente.",
                "Crisp guanciale in a pan.",
                "Whisk eggs and grated Pecorino together.",
                "Combine hot pasta with guanciale, remove from heat, stir in egg mixture quickly to form a creamy sauce.",
                "Season generously with freshly cracked black pepper."
            ],
            "dietary_flags": [],
            "calories": 650,
        },
        {
            "id": "mediterranean-quinoa-bowl",
            "title": "Mediterranean Quinoa Bowl",
            "cuisine": "Mediterranean",
            "prep_time_minutes": 15,
            "cook_time_minutes": 15,
            "ingredients": ["1 cup cooked quinoa", "1/2 cup cherry tomatoes", "1/2 cup cucumber", "1/4 cup feta cheese", "1/4 cup kalamata olives", "2 tbsp olive oil", "1 tbsp lemon juice"],
            "instructions": [
                "Fluff cooked quinoa into a bowl.",
                "Dice cucumber and cherry tomatoes.",
                "Arrange tomatoes, cucumber, olives, and crumbled feta over quinoa.",
                "Drizzle with olive oil and fresh lemon juice, toss before serving."
            ],
            "dietary_flags": ["vegetarian", "gluten-free"],
            "calories": 420,
        },
        {
            "id": "classic-avocado-toast",
            "title": "Classic Avocado Toast",
            "cuisine": "American",
            "prep_time_minutes": 5,
            "cook_time_minutes": 5,
            "ingredients": ["2 slices sourdough bread", "1 ripe avocado", "1 tbsp lemon juice", "Red pepper flakes", "Sea salt"],
            "instructions": [
                "Toast sourdough bread until golden.",
                "Mash ripe avocado with lemon juice and sea salt in a small bowl.",
                "Spread avocado mash generously on toast.",
                "Top with red pepper flakes and extra sea salt."
            ],
            "dietary_flags": ["vegan", "vegetarian"],
            "calories": 310,
        },
    ]

    print("Seeding 'recipes' collection...")
    for recipe in recipes:
        doc_id = recipe["id"]
        doc_ref = db.collection("recipes").document(doc_id)
        doc_ref.set(recipe)
        print(f"  - Added recipe: {recipe['title']} ({doc_id})")

    # 2. Seed Pantry Items
    pantry_items = [
        {"id": "eggs", "item_name": "Eggs", "quantity": 12.0, "unit": "pieces", "category": "Dairy/Protein"},
        {"id": "olive_oil", "item_name": "Olive Oil", "quantity": 500.0, "unit": "ml", "category": "Oils/Condiments"},
        {"id": "quinoa", "item_name": "Quinoa", "quantity": 1000.0, "unit": "grams", "category": "Grains"},
        {"id": "feta_cheese", "item_name": "Feta Cheese", "quantity": 200.0, "unit": "grams", "category": "Dairy"},
        {"id": "spaghetti", "item_name": "Spaghetti", "quantity": 500.0, "unit": "grams", "category": "Pasta"},
    ]

    print("Seeding 'pantry_items' collection...")
    for item in pantry_items:
        doc_id = item["id"]
        doc_ref = db.collection("pantry_items").document(doc_id)
        doc_ref.set(item)
        print(f"  - Added pantry item: {item['item_name']} ({doc_id})")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_firestore()
