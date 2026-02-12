# FastAPI backend entry point for QCalibrate
from fastapi import FastAPI
from app.routers.parser_handler import router as parser_router
from app.routers.topology_retriever import router as retriever_router
from app.routers.transpilers import router as transpilers_router
from app.routers.normalization_handler import router as normalization_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Enable CORS for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route handlers
app.include_router(parser_router)
app.include_router(retriever_router)
app.include_router(transpilers_router)
app.include_router(normalization_router)

