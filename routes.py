import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models import SessionLocal, Recipe, Tag, OCRData, AIRecommendation
from ai_service import extract_ocr_text, suggest_ingredients

router = APIRouter()

# -----------------------------------------------------------------------------
# Dependency – provide a DB session per request
# -----------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# Pydantic schemas (simple, no complex validators)
# -----------------------------------------------------------------------------

class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    ingredients: List[str] = Field(..., min_items=1)
    instructions: str = Field(..., min_length=10)
    tags: Optional[List[str]] = None

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[str] = None
    tags: Optional[List[str]] = None

class RecipeResponse(BaseModel):
    id: str
    title: str
    ingredients: List[str]
    instructions: str
    tags: List[str]
    created_at: str
    updated_at: str

class SearchResult(BaseModel):
    id: str
    title: str
    match_score: float

class OCRRequest(BaseModel):
    image: str  # base64‑encoded image data

class OCRResponse(BaseModel):
    extracted_text: str
    confidence: float

class SuggestRequest(BaseModel):
    dietary_restrictions: Optional[List[str]] = None

class SuggestResponse(BaseModel):
    suggestions: List[dict]

# -----------------------------------------------------------------------------
# Helper utilities
# -----------------------------------------------------------------------------

def _serialize_recipe(recipe: Recipe) -> RecipeResponse:
    # ingredients are stored as JSON string
    ingredients = json.loads(recipe.ingredients) if recipe.ingredients else []
    tag_names = [tag.name for tag in recipe.tags]
    return RecipeResponse(
        id=str(recipe.id),
        title=recipe.title,
        ingredients=ingredients,
        instructions=recipe.instructions,
        tags=tag_names,
        created_at=recipe.created_at.isoformat(),
        updated_at=recipe.updated_at.isoformat(),
    )

# -----------------------------------------------------------------------------
# CRUD endpoints
# -----------------------------------------------------------------------------

@router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db)):
    # Create or fetch tags first
    tag_objects = []
    if payload.tags:
        for name in payload.tags:
            tag = db.query(Tag).filter(Tag.name == name).first()
            if not tag:
                tag = Tag(name=name)
                db.add(tag)
                db.flush()
            tag_objects.append(tag)
    recipe = Recipe(
        title=payload.title,
        ingredients=json.dumps(payload.ingredients),
        instructions=payload.instructions,
        tags=tag_objects,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return _serialize_recipe(recipe)

@router.get("/recipes", response_model=List[RecipeResponse])
async def list_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    recipes = db.query(Recipe).offset(skip).limit(limit).all()
    return [_serialize_recipe(r) for r in recipes]

@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: str = Path(...), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return _serialize_recipe(recipe)

@router.put("/recipes/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    payload: RecipeUpdate,
    recipe_id: str = Path(...),
    db: Session = Depends(get_db),
):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if payload.title is not None:
        recipe.title = payload.title
    if payload.ingredients is not None:
        recipe.ingredients = json.dumps(payload.ingredients)
    if payload.instructions is not None:
        recipe.instructions = payload.instructions
    if payload.tags is not None:
        # Re‑sync tags
        new_tags = []
        for name in payload.tags:
            tag = db.query(Tag).filter(Tag.name == name).first()
            if not tag:
                tag = Tag(name=name)
                db.add(tag)
                db.flush()
            new_tags.append(tag)
        recipe.tags = new_tags
    db.commit()
    db.refresh(recipe)
    return _serialize_recipe(recipe)

@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(recipe_id: str = Path(...), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(recipe)
    db.commit()
    return None

# -----------------------------------------------------------------------------
# Search endpoint – combines simple ILIKE with AI ranking (fallback to DB order)
# -----------------------------------------------------------------------------

@router.get("/recipes/search", response_model=List[SearchResult])
async def search_recipes(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    # Basic DB filter (title or ingredient text)
    pattern = f"%{q}%"
    candidates = (
        db.query(Recipe)
        .filter(Recipe.title.ilike(pattern) | Recipe.ingredients.ilike(pattern))
        .all()
    )
    if not candidates:
        return []

    # Prepare messages for AI ranking
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that ranks recipes based on relevance to a user search query. Return JSON mapping recipe IDs to a relevance score between 0 and 1.",
        },
        {
            "role": "user",
            "content": f"Query: {q}\nRecipes: "
            + ", ".join([f"{str(r.id)}: {r.title}" for r in candidates]),
        },
    ]
    ai_response = await suggest_ingredients("search_ranking", [q])  # Dummy call just to reuse function signature
    # The AI service returns a dict; we expect it to contain a mapping "scores"
    scores = ai_response.get("scores", {})
    # Build result list, using AI score if present otherwise default 0.5
    results = []
    for r in candidates:
        score = float(scores.get(str(r.id), 0.5))
        results.append({"id": str(r.id), "title": r.title, "match_score": score})
    # Sort by descending match_score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results

# -----------------------------------------------------------------------------
# AI‑powered OCR endpoint
# -----------------------------------------------------------------------------

@router.post("/ocr/extract", response_model=OCRResponse)
async def ocr_extract(request: OCRRequest):
    ai_result = await extract_ocr_text(request.image)
    # Expected format: {"extracted_text": "...", "confidence": 0.95}
    return OCRResponse(**ai_result)

# -----------------------------------------------------------------------------
# AI‑powered ingredient substitution suggestions
# -----------------------------------------------------------------------------

@router.post("/recipes/{recipe_id}/suggest", response_model=SuggestResponse)
async def suggest_substitutions(
    recipe_id: str = Path(...),
    payload: SuggestRequest = Body(...),
    db: Session = Depends(get_db),
):
    # Verify recipe exists
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    ai_result = await suggest_ingredients(recipe_id, payload.dietary_restrictions or [])
    # Expected format: {"suggestions": [{"original": ..., "substitute": ..., "reason": ...}, ...]}
    return SuggestResponse(**ai_result)
