from fastapi import FastAPI
from app.routers.parser_handler import router as parser_router
from app.routers.topology_retriever import router as retriever_router
from app.routers.transpilers import router as transpilers_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(parser_router)
app.include_router(retriever_router)
app.include_router(transpilers_router)

