import asyncpg, os
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from time import time

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

raw_origins = os.getenv('ALLOWED_ORIGINS', '*')

# Normalize comma-separated origins from env (trims spaces and optional quotes).
allowed_origins = [o.strip().strip('"').strip("'") for o in raw_origins.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=['*'],
    allow_headers=['*']
)

RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '60'))
RATE_LIMIT_WINDOW_SEC = int(os.getenv('RATE_LIMIT_WINDOW_SEC', '60'))

# Keep limiter simple and local: per-IP, per-route in a rolling time window.
_request_buckets = defaultdict(deque)


@app.middleware('http')
async def rate_limit_middleware(request: Request, call_next):
    if not RATE_LIMIT_ENABLED:
        return await call_next(request)

    path = request.url.path
    method = request.method.upper()

    # Skip docs and preflight checks.
    if method == 'OPTIONS' or path in ['/', '/docs', '/openapi.json', '/redoc']:
        return await call_next(request)

    # Apply limiter only on API endpoints that can drive cost/load.
    if not (path.startswith('/chat') or path.startswith('/conversations')):
        return await call_next(request)

    forwarded_for = request.headers.get('x-forwarded-for', '')
    client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else ''
    if not client_ip:
        client_ip = request.client.host if request.client else 'unknown'

    key = f"{client_ip}:{method}:{path}"
    now = time()
    window_start = now - RATE_LIMIT_WINDOW_SEC
    bucket = _request_buckets[key]

    while bucket and bucket[0] <= window_start:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SEC - (now - bucket[0])))
        return JSONResponse(
            status_code=429,
            content={
                'detail': 'Rate limit exceeded. Please retry shortly.',
                'retry_after_sec': retry_after,
            },
            headers={'Retry-After': str(retry_after)},
        )

    bucket.append(now)
    return await call_next(request)

app.include_router(router)

@app.get('/')
async def root():
    return RedirectResponse(url='/docs')