"""Celery task definitions for the worker."""

from celery import shared_task

@shared_task
def process_optimization(job_id):
    return f"Job {job_id} processed"
