# QCal - Quantum Circuit Optimization Web App

## Project Overview

**QCal** is a web application for researchers and industry users to:

- Upload quantum circuits
- Optimize circuits for a given hardware architecture (qubit routing)
- Adapt optimization using qubit calibration data from multiple vendors
- Store and track optimization jobs
- Visualize circuit characteristics through a dashboard

The application is designed to be modular and scalable, supporting:

- User subscriptions and pay-per-use plans (monetization via Stripe)
- Organization/group management
- Multi-platform support (web, iOS, Windows, Linux)

---

## Features

### 1. Quantum Circuit Optimization
- Users can upload circuits in standard formats (QASM, JSON, etc.)
- Optimization algorithm performs:
  - Qubit routing according to hardware topology
  - Adaptation using calibration data to minimize gate errors
  - Fast execution initially in Python

### 2. Multi-Vendor Calibration Integration
- Vendor-specific topology and calibration data can be:
  - Uploaded manually by users, or
  - Fetched automatically via vendor APIs
- Ensures optimized circuits respect hardware fidelity constraints

### 3. Job Management & Dashboard
- Tracks job metadata: ID, user, organization, status, runtime stats
- Dashboard shows:
  - Circuit depth, gate counts, fidelity estimates
  - Comparison of original vs optimized circuits
  - Job history per user or organization

### 4. Authentication & Authorization
- Users log in via Supabase Auth (or Auth0)
- JWT tokens secure API requests
- Role-based access control for users, organizations, and plans
- Row-level security ensures users only access their data

### 5. Monetization
- Stripe integration supports:
  - Subscription plans
  - Pay-per-job credits
  - Tiered access to advanced optimizations and priority queues

---

## Architecture Overview

Frontend:
- Built with **React + TypeScript + Chakra UI + React Query**
- Hosted on **Vercel**
- Responsibilities:
  - User authentication and session management
  - File upload (quantum circuits, optional topology/calibration)
  - Polling job status and downloading optimized circuits
  - Displaying dashboards with circuit metrics

Backend API:
- Built with **FastAPI**
- Hosted on **Railway / Fly.io**
- Responsibilities:
  - Receive uploads and validate JWT
  - Store job metadata in **PostgreSQL** (Supabase)
  - Fetch vendor calibration/topology if needed
  - Enqueue optimization tasks to **Celery**
  - Return job ID / status to frontend

Task Queue:
- **Celery** with **Redis** broker
- Responsibilities:
  - Download input files from **Supabase Storage**
  - Run quantum optimization algorithm (qubit routing + calibration)
  - Upload optimized circuits back to **Supabase Storage**
  - Update job status in PostgreSQL

Database:
- **PostgreSQL** via **Supabase**
- Stores:
  - Users and organizations
  - Job metadata and status
  - Job runtime statistics

File Storage:
- **Supabase Storage**
- Stores:
  - Uploaded circuits
  - Hardware topology files
  - Calibration data
  - Optimized output files

Authentication:
- **Supabase Auth**
- Responsibilities:
  - User and organization management
  - JWT token issuance and validation
  - Role-based access control

Payment:
- **Stripe**
- Responsibilities:
  - Subscriptions and pay-per-use payments
  - Billing and quota enforcement
  - Integration with job limits / priority queues

Data Flow:
1. Frontend uploads circuit with JWT token
2. Backend validates request, stores file in Supabase Storage, inserts job metadata in PostgreSQL
3. Backend enqueues a Celery task via Redis
4. Celery worker downloads input files, runs optimization, uploads result
5. Backend updates job status in PostgreSQL
6. Frontend polls job status and displays dashboard metrics

---

## High-Level Folder Structure

QCal/
- README.md
- .gitignore
- frontend/  
  - React app with pages, components, services, and React Query hooks
- backend/  
  - FastAPI app with API routes, models, services (optimization logic), tasks (Celery), utils, and config
- celery_worker/  
  - Celery worker entry point, task definitions
- scripts/  
  - Database setup, seed scripts, vendor API fetch scripts
- docker/  
  - Dockerfiles and docker-compose for local dev or container deployment
- docs/  
  - Architecture diagrams, design documents, and project notes

---

## Modular Principles

- **Separation of Concerns**: Frontend UI is independent from backend API and task processing
- **Services Layer**: All business logic, vendor API calls, and optimization algorithms live in backend/services
- **Tasks Layer**: Celery tasks are isolated; only handle heavy computation and file I/O
- **Models & Schemas**: Backend models (SQLAlchemy) and schemas (Pydantic) are separate for clarity
- **Config & Secrets**: Centralized in backend/core/config.py and .env files
- **Utils**: Shared helpers (file handling, logging, validation) live in utils/

---

## Deployment Overview

- Frontend: Vercel, automatic GitHub deploys, free HTTPS
- Backend API & Workers: Railway / Fly.io containers
- Database & Auth: Supabase free tier
- Redis: Railway free tier or local Docker
- File Storage: Supabase Storage free tier
- Payment: Stripe for monetization

---

## Future Enhancements

- GPU or compiled backend optimization for performance
- Advanced analytics dashboards with circuit fidelity metrics
- Enterprise organization management with SSO
- Multi-queue Celery prioritization based on subscription plan
- Mobile-friendly dashboard using responsive React or React Native

---

## Summary

**QCal** provides a secure, modular, and scalable platform for:

- Optimizing quantum circuits for hardware backends
- Incorporating vendor calibration data
- Tracking and visualizing circuit metrics via dashboard
- Supporting monetization with subscription and pay-per-use models

The project uses modern frameworks and free-tier-friendly cloud services to allow MVP development with minimal cost while remaining extensible for future growth.
