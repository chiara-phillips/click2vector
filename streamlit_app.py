import streamlit as st
import random
import pandas as pd

# File to store recipes
DATA_FILE = "recipes.csv"

def load_recipes():
    # Load existing recipes
    try:
        df = pd.read_csv(DATA_FILE)
        return df.to_dict(orient='records')
    except FileNotFoundError:
        return []

def save_recipes(recipes):
    # Save recipes
    df = pd.DataFrame(recipes)
    df.to_csv(DATA_FILE, index=False)

def add_recipe(name, ingredients, servings):
    # Function to add a recipe with servings
    recipes = load_recipes()
    recipes.append({"name": name, "ingredients": ingredients, "servings": servings})
    save_recipes(recipes)

def edit_recipe(old_name, new_name, new_ingredients, new_servings):
    # Function to edit a recipe
    recipes = load_recipes()
    for recipe in recipes:
        if recipe["name"] == old_name:
            recipe["name"] = new_name
            recipe["ingredients"] = new_ingredients
            recipe["servings"] = new_servings
            break
    save_recipes(recipes)

def generate_meal_plan():
    # Function to generate a meal plan
    recipes = load_recipes()
    total_dinners = 7
    meal_plan = []
    remaining_dinners = total_dinners
    
    if not recipes:
        st.warning("No recipes available! Please add recipes first.")
        return []
    
    random.shuffle(recipes)
    
    while remaining_dinners > 0 and recipes:
        selected_recipe = recipes.pop()
        servings = int(selected_recipe.get("servings", 1))
        
        for _ in range(min(servings, remaining_dinners)):
            meal_plan.append({"name": selected_recipe["name"], "ingredients": selected_recipe["ingredients"], "type": "Cooking"})
        
        remaining_dinners -= servings
    
    return meal_plan

def generate_shopping_list(meal_plan):
    # Function to create a shopping list
    shopping_list = {}
    for meal in meal_plan:
        for ingredient in meal["ingredients"].split(','):
            ingredient = ingredient.strip()
            shopping_list[ingredient] = shopping_list.get(ingredient, 0) + 1
    return shopping_list

# Streamlit UI
st.title("😋 Weekly Meal Planner")

# Recipe Input
st.header("Add a Recipe")
recipe_name = st.text_input("Recipe Name:")
ingredients = st.text_area("Ingredients (comma separated):")
servings = st.number_input("Number of Dinners This Recipe Makes:", min_value=1, step=1, value=1)
if st.button("Save Recipe"):
    if recipe_name and ingredients:
        add_recipe(recipe_name, ingredients, servings)
        st.success(f"Recipe '{recipe_name}' saved!")
    else:
        st.error("Please enter both recipe name and ingredients.")

# Generate Meal Plan
st.header("Generate Weekly Meal Plan")
if st.button("Generate Plan"):
    meal_plan = generate_meal_plan()
    if meal_plan:
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        st.write("### Weekly Meal Plan:")
        for i, meal in enumerate(meal_plan):
            day = days_of_week[i % 7]
            st.write(f"{day}: **{meal['name']}**")
        
        # Generate Shopping List
        shopping_list = generate_shopping_list(meal_plan)
        st.write("### Shopping List:")
        for item, count in shopping_list.items():
            st.write(f"- {item} x{count}")

# Edit Recipe
st.header("Edit a Recipe")
recipes = load_recipes()
recipe_names = [recipe["name"] for recipe in recipes]
selected_recipe = st.selectbox("Select Recipe to Edit:", recipe_names)
if selected_recipe:
    selected_recipe_data = next(recipe for recipe in recipes if recipe["name"] == selected_recipe)
    new_recipe_name = st.text_input("New Recipe Name:", selected_recipe)
    new_ingredients = st.text_area("New Ingredients (comma separated):", selected_recipe_data["ingredients"])
    new_servings = st.number_input("New Number of Dinners This Recipe Makes:", min_value=1, step=1, value=int(selected_recipe_data["servings"]))
    if st.button("Update Recipe"):
        edit_recipe(selected_recipe, new_recipe_name, new_ingredients, new_servings)
        st.success(f"Recipe '{selected_recipe}' updated!")

# Show saved recipes
st.header("Saved Recipes")
if recipes:
    for recipe in recipes:
        st.write(f"- **{recipe['name']}**: {recipe['ingredients']} (Makes {recipe['servings']} dinners)")
else:
    st.write("No recipes saved yet.")
