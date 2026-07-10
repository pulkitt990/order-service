"""
Order Service — Self-Healing GitOps Demo App
A realistic microservice that:
  - Exposes /health for liveness/readiness probes
  - Exposes /metrics in Prometheus format
  - Has configurable failure mode (for the broken-version demo)
  - Tracks request latency, error rate, and request count per endpoint
"""

import os
import time
import random
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Config — controlled via environment variables
# FAILURE_RATE=0.0  → healthy (default)
# FAILURE_RATE=0.8  → 80% of requests fail (broken version demo)
# LATENCY_MS=0      → normal latency
# LATENCY_MS=2000   → simulate slow responses
# ──────────────────────────────────────────────
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.0"))   # 0.0 – 1.0
LATENCY_MS   = int(os.getenv("LATENCY_MS", "0"))         # extra ms per request

# ──────────────────────────────────────────────
# Prometheus Metrics
# ──────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "version"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint", "version"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)
ERROR_COUNTER = Counter(
    "http_errors_total",
    "Total HTTP errors (5xx)",
    ["endpoint", "version"],
)
ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Currently active HTTP requests",
    ["version"],
)
APP_INFO = Gauge(
    "app_info",
    "Application version info",
    ["version", "failure_rate"],
)

# ──────────────────────────────────────────────
# App startup
# ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    APP_INFO.labels(version=APP_VERSION, failure_rate=str(FAILURE_RATE)).set(1)
    logger.info(f"🚀 Order Service v{APP_VERSION} starting | failure_rate={FAILURE_RATE} | extra_latency={LATENCY_MS}ms")
    yield
    logger.info("🛑 Order Service shutting down")


app = FastAPI(
    title="Order Service",
    description="Self-Healing GitOps Demo — Microservice",
    version=APP_VERSION,
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# Middleware: track all requests automatically
# ──────────────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    ACTIVE_REQUESTS.labels(version=APP_VERSION).inc()
    start = time.perf_counter()

    try:
        # Inject artificial latency (for broken-version demo)
        if LATENCY_MS > 0:
            time.sleep(LATENCY_MS / 1000)

        response = await call_next(request)
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            version=APP_VERSION,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            version=APP_VERSION,
        ).observe(duration)

        if response.status_code >= 500:
            ERROR_COUNTER.labels(endpoint=request.url.path, version=APP_VERSION).inc()

        return response

    except Exception as exc:
        duration = time.perf_counter() - start
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=500,
            version=APP_VERSION,
        ).inc()
        ERROR_COUNTER.labels(endpoint=request.url.path, version=APP_VERSION).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            version=APP_VERSION,
        ).observe(duration)
        raise exc
    finally:
        ACTIVE_REQUESTS.labels(version=APP_VERSION).dec()


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/health", tags=["ops"])
async def health():
    """Kubernetes liveness + readiness probe endpoint."""
    return {"status": "healthy", "version": APP_VERSION}


@app.get("/metrics", tags=["ops"])
async def metrics():
    """Prometheus metrics scrape endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/", tags=["app"])
async def root():
    return {"service": "order-service", "version": APP_VERSION, "status": "running"}


@app.get("/orders", tags=["app"])
async def list_orders():
    """List orders — simulates real workload."""
    _maybe_fail("/orders")
    orders = [
        {"id": f"ORD-{random.randint(1000,9999)}", "item": item, "status": "confirmed"}
        for item in random.sample(["Laptop", "Phone", "Tablet", "Monitor", "Keyboard"], 3)
    ]
    return {"orders": orders, "count": len(orders), "version": APP_VERSION}


@app.post("/orders", tags=["app"])
async def create_order(request: Request):
    """Create an order — write path, higher error visibility."""
    _maybe_fail("/orders")
    body = await request.json()
    return {
        "id": f"ORD-{random.randint(1000,9999)}",
        "item": body.get("item", "Unknown"),
        "status": "created",
        "version": APP_VERSION,
    }


@app.get("/orders/{order_id}", tags=["app"])
async def get_order(order_id: str):
    """Get a specific order."""
    _maybe_fail(f"/orders/{{id}}")
    return {
        "id": order_id,
        "item": "Sample Item",
        "status": "confirmed",
        "version": APP_VERSION,
    }


# ──────────────────────────────────────────────
# Helper: inject failures for demo
# ──────────────────────────────────────────────
def _maybe_fail(endpoint: str):
    """Randomly fail based on FAILURE_RATE env var."""
    if FAILURE_RATE > 0 and random.random() < FAILURE_RATE:
        logger.warning(f"💥 Injecting failure on {endpoint} (rate={FAILURE_RATE})")
        raise HTTPException(
            status_code=500,
            detail=f"Simulated failure — version {APP_VERSION} is broken",
        )
