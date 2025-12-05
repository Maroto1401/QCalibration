from pydantic import BaseModel
from typing import Any, Optional

class JobCreate(BaseModel):
    user_id: int
    input_file: str

class JobOut(BaseModel):
    id: int
    status: str
    metadata: Optional[Any] = None
