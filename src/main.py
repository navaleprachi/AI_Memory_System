import asyncpg, os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

load_dotenv()

from src.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create a connection pool
    app.state.db = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
    print("Database pool ready")
    yield
    # Shutdown: Close the connection pool
    await app.state.db.close()

app = FastAPI(title='AI Memory System', lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

app.include_router(router)

@app.get('/')
async def root():
    return RedirectResponse(url='/docs')