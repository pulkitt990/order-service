"""
Unit tests for the Order Service.
Tests: health endpoint, orders CRUD, metrics endpoint, failure injection.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set environment before importing app
os.environ["APP_VERSION"] = "test-1.0.0"
os.environ["FAILURE_RATE"] = "0.0"
os.environ["LATENCY_MS"] = "0"

from src.main import app

client = TestClient(app)


# ──────────────────────────────────────────────
# Health endpoint
# ──────────────────────────────────────────────
def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_version():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ──────────────────────────────────────────────
# Metrics endpoint
# ──────────────────────────────────────────────
def test_metrics_endpoint_returns_200():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_contains_prometheus_format():
    response = client.get("/metrics")
    # Prometheus text format always contains TYPE comments
    assert b"# HELP" in response.content or b"# TYPE" in response.content


# ──────────────────────────────────────────────
# Orders API
# ──────────────────────────────────────────────
def test_list_orders_returns_200():
    response = client.get("/orders")
    assert response.status_code == 200


def test_list_orders_returns_list():
    response = client.get("/orders")
    data = response.json()
    assert "orders" in data
    assert isinstance(data["orders"], list)
    assert data["count"] == len(data["orders"])


def test_create_order_returns_201_ish():
    response = client.post("/orders", json={"item": "Laptop"})
    assert response.status_code == 200
    data = response.json()
    assert data["item"] == "Laptop"
    assert data["status"] == "created"
    assert data["id"].startswith("ORD-")


def test_get_order_by_id():
    response = client.get("/orders/ORD-1234")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ORD-1234"


# ──────────────────────────────────────────────
# Failure injection
# ──────────────────────────────────────────────
def test_full_failure_rate_always_errors(monkeypatch):
    monkeypatch.setenv("FAILURE_RATE", "1.0")
    # Reimport to pick up new env var
    import importlib
    import src.main as main_module
    importlib.reload(main_module)

    from fastapi.testclient import TestClient as TC
    broken_client = TC(main_module.app)

    response = broken_client.get("/orders")
    assert response.status_code == 500


def test_zero_failure_rate_never_errors():
    # Default client has FAILURE_RATE=0.0
    for _ in range(10):
        response = client.get("/orders")
        assert response.status_code == 200
