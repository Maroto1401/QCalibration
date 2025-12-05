                    ┌───────────────────┐
                    │  React Frontend   │
                    │ (Vercel Hosting) │
                    │                   │
                    │ - Login / Signup │
                    │ - Upload circuit │
                    │ - Job status     │
                    │ - Download result│
                    └────────┬─────────┘
                             │ HTTPS / API
                             │
                             ▼
                    ┌───────────────────┐
                    │  FastAPI Backend  │
                    │ (Railway / Fly.io)│
                    │                   │
                    │ - Receive uploads │
                    │ - Validate inputs │
                    │ - Store job metadata in PostgreSQL
                    │ - Enqueue optimization task to Celery
                    │ - Optional: Fetch vendor topology/calibration
                    │ - Return job ID / status
                    └────────┬─────────┘
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
        ┌───────────────┐        ┌───────────────┐
        │ Redis Broker  │        │ PostgreSQL    │
        │ (Celery queue)│        │ (Supabase DB) │
        │               │        │ - Job metadata│
        │ - Handles task│        │ - Users       │
        │   queuing     │        │ - Organizations│
        └───────┬───────┘        └───────┬───────┘
                │                        │
                ▼                        ▼
        ┌───────────────┐         ┌───────────────┐
        │ Celery Worker │         │ Supabase Auth │
        │ (Railway /    │         │ or Auth0      │
        │ Fly.io)       │         │ - JWT Tokens  │
        │ - Downloads   │         │ - User mgmt   │
        │   files from  │         │ - Plan/Role   │
        │   Supabase    │         │   info        │
        │   Storage     │         └───────────────┘
        │ - Runs quantum│
        │   optimization│
        │ - Uploads     │
        │   optimized   │
        │   files       │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Supabase      │
        │ Storage       │
        │ - Input files │
        │ - Topology    │
        │ - Calibration │
        │ - Optimized   │
        │   outputs     │
        └───────────────┘
