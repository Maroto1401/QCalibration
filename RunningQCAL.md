# Running QCal - Quantum Circuit Optimization Web App

## Overview

**QCal** is a web application for researchers and industry to:

- Upload quantum circuits
- Optimize circuits for hardware architectures (qubit routing)
- Adapt optimization using qubit calibration data
- Track and visualize job metrics in a dashboard

This guide explains how to run **all components locally**.

---

## Prerequisites

- Python 3.12+  
- Node.js 18+  
- Homebrew (for Redis)  
- VSCode or terminal  
- Supabase account (for database & storage)

---

## 1️⃣ Clone Repository

git clone <your-repo-url> QCal
cd QCal

---

## 2️⃣ Backend Setup (FastAPI)

1. Create and activate Python virtual environment:

python3 -m venv venv
source venv/bin/activate

2. Install backend dependencies:

pip install --upgrade pip
pip install -r backend/requirements.txt

3. Create `.env` in project root with the following content:

REDIS_URL=redis://localhost:6379/0
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
DATABASE_URL=postgresql://user:password@host:port/dbname

4. Run backend server:

cd backend
uvicorn main:app --reload

- Backend runs at http://127.0.0.1:8000/
- Test in browser: should show welcome message

---

## 3️⃣ Redis Setup (Broker for Celery)

Install and start Redis using Homebrew:

brew install redis
brew services start redis

Test Redis is running:

redis-cli ping
# Expected output: PONG

---

## 4️⃣ Celery Worker Setup

1. Activate Python virtual environment if not already active:

source venv/bin/activate

2. Start Celery worker:

cd celery_worker

celery -A worker.celery_app worker --loglevel=info

- Worker listens for tasks from the backend

3. Optional: test a dummy task:

from celery_worker.worker import test_task
result = test_task.delay()
print(result.get(timeout=10))
# Expected output: "Celery is working!"

---

## 5️⃣ Frontend Setup (React + TypeScript + Chakra UI)

1. Navigate to frontend folder:

cd frontend

2. Install dependencies:

npm install

3. Start frontend development server:

npm start

- Opens browser at http://localhost:3000
- API requests are proxied to backend (http://127.0.0.1:8000)


## 7️⃣ Notes & Tips

- Always activate the **Python virtual environment** before running backend or Celery
- **Redis must be running** before starting Celery
- Frontend and backend should run in **separate terminals**
- Homebrew Redis is fine for development; Docker can be added later for isolation
- Use VSCode Python interpreter from your `venv` for correct environment

