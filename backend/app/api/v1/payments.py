from fastapi import APIRouter

router = APIRouter()

@router.get("/payments/status")
def status():
    return {"stripe": "placeholder"}
