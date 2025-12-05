"""Celery task definition placeholder."""

from celery import Celery

celery_app = Celery('qcal', broker='redis://localhost:6379/0')

@celery_app.task
def optimize_circuit(job_id: int):
    print(f"Optimizing job {job_id}")
    return {"status": "completed"}
