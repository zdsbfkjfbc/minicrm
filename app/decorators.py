"""Decorators for Flask routes — authorization and utilities."""

from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def require_gestor(f):
    """Decorator that restricts a route to users with role 'Gestor'.

    Combines @login_required with a role check so routes only need
    one decorator instead of repeating the guard block.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'Gestor':
            flash('Acesso negado. Apenas Gestores podem acessar esta página.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
