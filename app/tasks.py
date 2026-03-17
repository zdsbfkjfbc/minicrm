import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

from flask import current_app

from app import db
from app.models import User
from app.services.importer import build_contacts

executor = ThreadPoolExecutor(max_workers=2)
JOB_STATUS: dict[str, str] = {}
JOB_OWNER: dict[str, int] = {}


def _run_import(job_id: str, payload: str, user_id: int, app):
    JOB_STATUS[job_id] = 'running'
    with app.app_context():
        try:
            contacts, errors = build_contacts(payload, user_id)
            if errors:
                JOB_STATUS[job_id] = f"errors: {len(errors)}"
                return
            db.session.add_all(contacts)
            db.session.commit()
            JOB_STATUS[job_id] = f'completed ({len(contacts)} contatos)'
        except Exception as exc:
            logging.getLogger('app.tasks').exception("Erro na importação assíncrona")
            JOB_STATUS[job_id] = f'error: {exc}'


def enqueue_import_job(payload: str, user_id: int) -> str:
    job_id = str(uuid.uuid4())
    JOB_STATUS[job_id] = 'pending'
    app = current_app._get_current_object()
    JOB_OWNER[job_id] = user_id
    executor.submit(_run_import, job_id, payload, user_id, app)
    return job_id


def get_job_status(job_id: str, requester_id: int) -> str | None:
    owner = JOB_OWNER.get(job_id)
    if owner != requester_id:
        return None
    return JOB_STATUS.get(job_id)
