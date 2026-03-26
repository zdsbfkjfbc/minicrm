from flask import request
from app.domain.use_cases import manage_auth as auth_uc

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_MINUTES = 15
LOGIN_BLOCK_MINUTES = 15

LOGIN_ATTEMPTS: dict[tuple[str, str], list] = {}

def _client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'
def is_login_blocked(attempts: dict, username: str) -> tuple[bool, int]:
    return auth_uc.is_login_blocked(attempts, _client_ip(), username)


def register_login_failure(attempts: dict, username: str):
    auth_uc.register_login_failure(attempts, _client_ip(), username)


def clear_login_failures(attempts: dict, username: str):
    auth_uc.clear_login_failures(attempts, _client_ip(), username)
