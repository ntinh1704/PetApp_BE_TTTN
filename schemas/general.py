from pydantic import BaseModel
from typing import Optional
class ID_NAME(BaseModel):
    id:Optional[int]=None
    name:Optional[str]=None
class ListGeneral(BaseModel):
    total_pages:int
    total_elements:int
    has_next:bool