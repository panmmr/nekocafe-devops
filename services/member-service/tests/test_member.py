"""Tests for Member Service"""
import os
import pytest
from fastapi.testclient import TestClient

os.environ["MEMBER_DB_PATH"] = ":memory:"
from src.main import app
from src.database import init_db

init_db()
client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["service"] == "member-service"


class TestAuth:
    def test_register_success(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138001", "smsCode": "123456", "nickname": "测试猫友"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "accessToken" in data
        assert "refreshToken" in data

    def test_register_duplicate(self):
        client.post("/api/v1/auth/register", json={
            "phone": "13800138002", "smsCode": "123456"
        })
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138002", "smsCode": "123456"
        })
        assert resp.status_code == 409

    def test_login_success(self):
        resp = client.post("/api/v1/auth/login", json={
            "phone": "13800138001", "smsCode": "123456"
        })
        assert resp.status_code == 200
        assert "accessToken" in resp.json()

    def test_login_user_not_found(self):
        resp = client.post("/api/v1/auth/login", json={
            "phone": "19900000000", "smsCode": "123456"
        })
        assert resp.status_code == 401

    def test_refresh_token(self):
        reg = client.post("/api/v1/auth/register", json={
            "phone": "13800138003", "smsCode": "123456"
        })
        refresh = reg.json()["refreshToken"]
        resp = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh})
        assert resp.status_code == 200
        assert "accessToken" in resp.json()


class TestMemberProfile:
    def _get_headers(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138010", "smsCode": "123456"
        })
        token = resp.json()["accessToken"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_profile(self):
        headers = self._get_headers()
        resp = client.get("/api/v1/members/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "memberId" in data
        assert "nickname" in data

    def test_get_profile_unauthorized(self):
        resp = client.get("/api/v1/members/me")
        assert resp.status_code == 401

    def test_get_level(self):
        headers = self._get_headers()
        resp = client.get("/api/v1/members/me/level", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["currentLevel"] == "NORMAL"


class TestPoints:
    def _get_headers(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138020", "smsCode": "123456"
        })
        return {"Authorization": f"Bearer {resp.json()['accessToken']}"}

    def test_get_points(self):
        resp = client.get("/api/v1/members/me/points", headers=self._get_headers())
        assert resp.status_code == 200

    def test_exchange_insufficient(self):
        resp = client.post("/api/v1/members/me/points/exchange",
                           json={"rewardId": 1}, headers=self._get_headers())
        assert resp.status_code == 400


class TestCoupons:
    def _get_headers(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138030", "smsCode": "123456"
        })
        return {"Authorization": f"Bearer {resp.json()['accessToken']}"}

    def test_get_coupons(self):
        resp = client.get("/api/v1/members/me/coupons", headers=self._get_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2


class TestUserCat:
    def _get_headers(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138040", "smsCode": "123456"
        })
        return {"Authorization": f"Bearer {resp.json()['accessToken']}"}

    def test_create_and_list_cats(self):
        headers = self._get_headers()
        resp = client.post("/api/v1/members/me/cats", json={
            "name": "小雪", "breed": "布偶",
            "age": 2, "personalityTags": ["安静粘人"]
        }, headers=headers)
        assert resp.status_code == 201
        resp = client.get("/api/v1/members/me/cats", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["name"] == "小雪"

    def test_delete_cat(self):
        headers = self._get_headers()
        resp = client.post("/api/v1/members/me/cats", json={
            "name": "小黑", "breed": "英短"
        }, headers=headers)
        cat_id = 1
        resp = client.delete(f"/api/v1/members/me/cats/{cat_id}", headers=headers)
        assert resp.status_code == 204


class TestPrivacy:
    def _get_headers(self):
        resp = client.post("/api/v1/auth/register", json={
            "phone": "13800138050", "smsCode": "123456"
        })
        return {"Authorization": f"Bearer {resp.json()['accessToken']}"}

    def test_export_data(self):
        resp = client.post("/api/v1/members/me/data/export", headers=self._get_headers())
        assert resp.status_code == 202

    def test_delete_data(self):
        resp = client.post("/api/v1/members/me/data/delete", headers=self._get_headers())
        assert resp.status_code == 202
