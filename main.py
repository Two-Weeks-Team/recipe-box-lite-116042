import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from models import Base, engine
from routes import router

app = FastAPI(title="Recipe Box Lite", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)

# Health check
@app.get("/health", response_model=dict)
async def health_check():
    return {"status": "ok"}

# Simple landing page
@app.get("/", response_class=HTMLResponse)
async def root():
    html = """
    <html>
    <head>
        <title>Recipe Box Lite</title>
        <style>
            body {background-color:#1e1e1e;color:#e5e5e5;font-family:Arial,Helvetica,sans-serif;padding:2rem;}
            a {color:#58a6ff;}
            h1 {color:#ff7b72;}
            table {border-collapse:collapse;width:100%;margin-top:1rem;}
            th, td {border:1px solid #444;padding:0.5rem;text-align:left;}
            th {background:#2d2d2d;}
        </style>
    </head>
    <body>
        <h1>Recipe Box Lite</h1>
        <p>A simple, privacy‑first digital cookbook.</p>
        <h2>Available API Endpoints</h2>
        <table>
            <tr><th>Method</th><th>Path</th><th>Description</th></tr>
            <tr><td>GET</td><td>/health</td><td>Health check</td></tr>
            <tr><td>POST</td><td>/api/recipes</td><td>Create a new recipe</td></tr>
            <tr><td>GET</td><td>/api/recipes</td><td>List all recipes</td></tr>
            <tr><td>GET</td><td>/api/recipes/{id}</td><td>Get a recipe by ID</td></tr>
            <tr><td>PUT</td><td>/api/recipes/{id}</td><td>Update a recipe</td></tr>
            <tr><td>DELETE</td><td>/api/recipes/{id}</td><td>Delete a recipe</td></tr>
            <tr><td>GET</td><td>/api/recipes/search</td><td>Search recipes (AI‑enhanced)</td></tr>
            <tr><td>POST</td><td>/api/ocr/extract</td><td>AI OCR extraction (AI‑powered)</td></tr>
            <tr><td>POST</td><td>/api/recipes/{id}/suggest</td><td>Ingredient substitution suggestions (AI‑powered)</td></tr>
        </table>
        <p>Tech Stack: FastAPI 0.115, SQLAlchemy 2.0, PostgreSQL, DigitalOcean Serverless Inference (openai‑gpt‑oss‑120b).</p>
        <p>Docs: <a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

# Include API router under /api prefix
app.include_router(router, prefix="/api")
