"""Unit tests for auth rate-limit logic — no Flask."""

import pytest
from datetime import datetime, timezone

from app.domain.use_cases.manage_auth import (
    clear_login_failures,
    is_login_blocked,
    register_login_failure,
    MAX_LOGIN_ATTEMPTS,
)


class TestRateLimit:
    def test_not_blocked_initially(self):
        attempts = {}
        blocked, _ = is_login_blocked(attempts, "127.0.0.1", "user")
        assert blocked is False

    def test_blocked_after_max_attempts(self):
        attempts = {}
        for _ in range(MAX_LOGIN_ATTEMPTS):
            register_login_failure(attempts, "127.0.0.1", "user")
        blocked, retry = is_login_blocked(attempts, "127.0.0.1", "user")
        assert blocked is True
        assert retry > 0

    def test_clear_resets_attempts(self):
        attempts = {}
        for _ in range(MAX_LOGIN_ATTEMPTS):
            register_login_failure(attempts, "127.0.0.1", "user")
        clear_login_failures(attempts, "127.0.0.1", "user")
        blocked, _ = is_login_blocked(attempts, "127.0.0.1", "user")
        assert blocked is False

    def test_different_users_are_independent(self):
        attempts = {}
        for _ in range(MAX_LOGIN_ATTEMPTS):
            register_login_failure(attempts, "127.0.0.1", "user_a")
        blocked, _ = is_login_blocked(attempts, "127.0.0.1", "user_b")
        assert blocked is False

    def test_case_insensitive_username(self):
        attempts = {}
        for _ in range(MAX_LOGIN_ATTEMPTS):
            register_login_failure(attempts, "127.0.0.1", "Admin")
        blocked, _ = is_login_blocked(attempts, "127.0.0.1", "admin")
        assert blocked is True
