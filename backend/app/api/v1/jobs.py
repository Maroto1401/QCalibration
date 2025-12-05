from fastapi import APIRouter

router = APIRouter()

@router.get("/jobs")
def list_jobs():
    return {"jobs": []}
