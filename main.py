import os
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import IntegrityError
import uvicorn

# Database Setup
DATABASE_URL = "sqlite:///./data/recipes.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Model
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cuisine = Column(String)
    prep_time = Column(String)
    cook_time = Column(String)
    servings = Column(String)
    ingredients = Column(Text)
    instructions = Column(Text)
    image_color = Column(String) # Placeholder for image color block

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Seed Database
def seed_database(db: Session):
    if db.query(Recipe).count() == 0:
        recipes_data = [
            {
                "name": "Spaghetti Carbonara",
                "cuisine": "Italian",
                "prep_time": "15 min",
                "cook_time": "20 min",
                "servings": "4",
                "ingredients": "Pasta, Eggs, Pecorino Romano, Guanciale/Pancetta, Black Pepper",
                "instructions": "1. Cook pasta. 2. Fry guanciale. 3. Mix eggs, cheese, pepper. 4. Combine all.",
                "image_color": "#F4A261"
            },
            {
                "name": "Chicken Tikka Masala",
                "cuisine": "Indian",
                "prep_time": "30 min",
                "cook_time": "45 min",
                "servings": "6",
                "ingredients": "Chicken, Yogurt, Spices, Tomatoes, Cream",
                "instructions": "1. Marinate chicken. 2. Cook chicken. 3. Make sauce. 4. Combine.",
                "image_color": "#E76F51"
            },
            {
                "name": "Beef Tacos",
                "cuisine": "Mexican",
                "prep_time": "20 min",
                "cook_time": "25 min",
                "servings": "4",
                "ingredients": "Ground Beef, Tortillas, Lettuce, Cheese, Salsa, Taco Seasoning",
                "instructions": "1. Cook beef. 2. Warm tortillas. 3. Assemble tacos.",
                "image_color": "#2A9D8F"
            },
            {
                "name": "Sushi Rolls",
                "cuisine": "Japanese",
                "prep_time": "60 min",
                "cook_time": "0 min",
                "servings": "2",
                "ingredients": "Sushi Rice, Nori, Fish, Avocado, Cucumber",
                "instructions": "1. Cook sushi rice. 2. Prepare fillings. 3. Roll sushi.",
                "image_color": "#E9C46A"
            },
            {
                "name": "French Onion Soup",
                "cuisine": "French",
                "prep_time": "20 min",
                "cook_time": "60 min",
                "servings": "4",
                "ingredients": "Onions, Beef Broth, Baguette, Gruyere Cheese, Butter",
                "instructions": "1. Caramelize onions. 2. Add broth. 3. Toast bread, melt cheese.",
                "image_color": "#DDA15E"
            },
            {
                "name": "Pad Thai",
                "cuisine": "Thai",
                "prep_time": "25 min",
                "cook_time": "30 min",
                "servings": "2",
                "ingredients": "Rice Noodles, Shrimp/Tofu, Peanuts, Bean Sprouts, Egg, Tamarind Sauce",
                "instructions": "1. Soak noodles. 2. Cook protein. 3. Stir-fry with sauce and veggies.",
                "image_color": "#F5D491"
            },
            {
                "name": "Mediterranean Salad",
                "cuisine": "Mediterranean",
                "prep_time": "15 min",
                "cook_time": "0 min",
                "servings": "3",
                "ingredients": "Cucumbers, Tomatoes, Feta, Olives, Red Onion, Olive Oil, Lemon Juice",
                "instructions": "1. Chop veggies. 2. Crumble feta. 3. Dress and serve.",
                "image_color": "#8BC34A"
            },
            {
                "name": "Classic Lasagna",
                "cuisine": "Italian",
                "prep_time": "30 min",
                "cook_time": "60 min",
                "servings": "8",
                "ingredients": "Lasagna Noodles, Ground Beef, Ricotta, Mozzarella, Marinara Sauce",
                "instructions": "1. Cook meat sauce. 2. Layer noodles, sauce, cheese. 3. Bake.",
                "image_color": "#CD5C5C"
            },
        ]
        for recipe_data in recipes_data:
            recipe = Recipe(**recipe_data)
            db.add(recipe)
        db.commit()
        print("Database seeded with initial recipes.")

# FastAPI App Setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Ensure 'data' directory exists for SQLite
os.makedirs("data", exist_ok=True)

# Seed the database on startup
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    seed_database(db)
    db.close()

# Routes
@app.get("/health", response_class=HTMLResponse)
async def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    recipes = db.query(Recipe).all()
    return templates.TemplateResponse("home.html", {"request": request, "recipes": recipes})

@app.get("/recipes/{recipe_id}", response_class=HTMLResponse)
async def recipe_detail(request: Request, recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    # Split ingredients and instructions into lists for easier display
    recipe.ingredients_list = [item.strip() for item in recipe.ingredients.split(',') if item.strip()]
    recipe.instructions_list = [item.strip() for item in recipe.instructions.split('.') if item.strip()]
    return templates.TemplateResponse("recipe_detail.html", {"request": request, "recipe": recipe})

@app.get("/add_recipe", response_class=HTMLResponse)
async def add_recipe_form(request: Request):
    return templates.TemplateResponse("add_recipe.html", {"request": request, "message": None, "error": None})

@app.post("/add_recipe", response_class=HTMLResponse)
async def add_recipe_submit(
    request: Request,
    name: str = Form(...),
    cuisine: str = Form(...),
    prep_time: str = Form(...),
    cook_time: str = Form(...),
    servings: str = Form(...),
    ingredients: str = Form(...),
    instructions: str = Form(...),
    image_color: Optional[str] = Form("#cccccc"), # Default color
    db: Session = Depends(get_db)
):
    try:
        new_recipe = Recipe(
            name=name,
            cuisine=cuisine,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            ingredients=ingredients,
            instructions=instructions,
            image_color=image_color
        )
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
        return RedirectResponse(url=app.url_path_for("home"), status_code=303)
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            "add_recipe.html",
            {"request": request, "error": "Failed to add recipe. Please check your input.", "message": None}
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "add_recipe.html",
            {"request": request, "error": f"An unexpected error occurred: {e}", "message": None}
        )

@app.get("/search", response_class=HTMLResponse)
async def search_recipes(request: Request, query: str = "", db: Session = Depends(get_db)):
    recipes = []
    if query:
        search_pattern = f"%{query}%"
        recipes = db.query(Recipe).filter(
            (Recipe.name.ilike(search_pattern)) |
            (Recipe.ingredients.ilike(search_pattern)) |
            (Recipe.cuisine.ilike(search_pattern))
        ).all()
    return templates.TemplateResponse("search_results.html", {"request": request, "recipes": recipes, "query": query})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
