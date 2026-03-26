"""Use case for authentication rate-limiting — testable without Flask."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_MINUTES = 15
LOGIN_BLOCK_MINUTES = 15


def _purge_old_attempts(
    attempts: dict[tuple[str, str], list[datetime]], now: datetime
) -> None:
    cutoff = now - timedelta(minutes=LOGIN_WINDOW_MINUTES)
    for key in list(attempts.keys()):
        fresh = [ts for ts in attempts[key] if ts >= cutoff]
        if fresh:
            attempts[key] = fresh
        else:
            del attempts[key]


def is_login_blocked(
    attempts: dict[tuple[str, str], list[datetime]],
    client_ip: str,
    username: str,
) -> tuple[bool, int]:
    """Check if a login attempt should be blocked.

    Returns (is_blocked, retry_after_seconds).
    """
    now = datetime.now(timezone.utc)
    _purge_old_attempts(attempts, now)
    key = (client_ip, username.strip().lower())
    entry = attempts.get(key, [])
    if len(entry) < MAX_LOGIN_ATTEMPTS:
        return False, 0
    first_attempt = entry[0]
    blocked_until = first_attempt + timedelta(minutes=LOGIN_BLOCK_MINUTES)
    if blocked_until <= now:
        attempts.pop(key, None)
        return False, 0
    retry_seconds = int((blocked_until - now).total_seconds())
    return True, max(retry_seconds, 1)


def register_login_failure(
    attempts: dict[tuple[str, str], list[datetime]],
    client_ip: str,
    username: str,
) -> None:
    now = datetime.now(timezone.utc)
    _purge_old_attempts(attempts, now)
    key = (client_ip, username.strip().lower())
    attempts.setdefault(key, []).append(now)


def clear_login_failures(
    attempts: dict[tuple[str, str], list[datetime]],
    client_ip: str,
    username: str,
) -> None:
    attempts.pop((client_ip, username.strip().lower()), None)
