"""Tests for Reservation Service"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db, DB_PATH
import os

os.environ["RESERVATION_DB_PATH"] = ":memory:"
init_db()

client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "reservation-service"

    def test_ready(self):
        resp = client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"


class TestAvailability:
    def test_get_availability(self):
        resp = client.get("/api/v1/stores/1/availability?date=2026-06-15&guestCount=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["storeId"] == 1
        assert len(data["timeSlots"]) > 0
        slot = data["timeSlots"][0]
        assert "timeSlot" in slot
        assert "availableSlots" in slot

    def test_invalid_date_format(self):
        resp = client.get("/api/v1/stores/1/availability?date=15-06-2026")
        assert resp.status_code == 422


class TestReservationCRUD:
    def test_create_reservation(self):
        resp = client.post("/api/v1/reservations", json={
            "storeId": 1, "date": "2026-06-15", "timeSlot": "10:00-12:00",
            "guestCount": 2, "bringCat": False
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["reservationId"] > 0
        assert data["status"] == "CONFIRMED"

    def test_create_full_slot(self):
        # Fill up 10:00-12:00 slot (capacity 16 across 4 tables)
        for _ in range(20):
            client.post("/api/v1/reservations", json={
                "storeId": 1, "date": "2026-06-15", "timeSlot": "10:00-12:00",
                "guestCount": 2
            })
        resp = client.post("/api/v1/reservations", json={
            "storeId": 1, "date": "2026-06-15", "timeSlot": "10:00-12:00",
            "guestCount": 2
        })
        assert resp.status_code == 409

    def test_get_reservation_not_found(self):
        resp = client.get("/api/v1/reservations/99999")
        assert resp.status_code == 404

    def test_cancel_reservation(self):
        resp = client.post("/api/v1/reservations", json={
            "storeId": 1, "date": "2026-06-17", "timeSlot": "14:00-16:00",
            "guestCount": 1
        })
        rid = resp.json()["reservationId"]
        resp = client.post(f"/api/v1/reservations/{rid}/cancel")
        assert resp.status_code == 200
        assert "缓冲池" in resp.json()["message"]


class TestQueue:
    def test_join_queue(self):
        resp = client.post("/api/v1/stores/1/queue")
        assert resp.status_code == 201
        data = resp.json()
        assert data["ticketId"] > 0
        assert data["status"] == "WAITING"

    def test_get_queue_progress(self):
        resp = client.post("/api/v1/stores/1/queue")
        tid = resp.json()["ticketId"]
        resp = client.get(f"/api/v1/queue/{tid}")
        assert resp.status_code == 200
        assert "aheadCount" in resp.json()

    def test_cancel_queue(self):
        resp = client.post("/api/v1/stores/1/queue")
        tid = resp.json()["ticketId"]
        resp = client.delete(f"/api/v1/queue/{tid}")
        assert resp.status_code == 204


class TestCatMatching:
    def test_match(self):
        resp = client.post("/api/v1/reservations/match", json={
            "storeId": 1, "userId": 1, "userCatId": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["recommendations"]) <= 3


class TestMetrics:
    def test_metrics_endpoint(self):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text or "prometheus" in resp.text.lower()
