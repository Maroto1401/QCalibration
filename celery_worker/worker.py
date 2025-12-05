"""Celery worker initialization."""

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()  # load REDIS_URL from .env

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "QCalibration",
    broker=REDIS_URL,
    backend=REDIS_URL
)

@celery_app.task
def test_task():
    return "Celery is working!"
