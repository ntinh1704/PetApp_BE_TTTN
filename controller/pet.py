from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from crud import pet_crud
from db.database import get_db
from schemas.pet_schema import PetCreate, PetUpdate
from setting.utils import (
    get_offset_limit,
    get_pages_records,
    get_current_user,
    get_current_user,
)


def create_pet(data: PetCreate, current_user=Depends(get_current_user)):
    db_api = pet_crud.PetDatabaseApi(current_user)
    return db_api.create_pet(data)


def get_list_pet(
    text_search: str = None,
    current_user=Depends(get_current_user),
    offset_limit=Depends(get_offset_limit),
):
    db_api = pet_crud.PetDatabaseApi(current_user)
    offset, limit = offset_limit
    data, total = db_api.get_list_pet(offset, limit, text_search)
    return get_pages_records((data, total), offset_limit)


def get_pet_by_id(pet_id: int, current_user=Depends(get_current_user)):
    db_api = pet_crud.PetDatabaseApi(current_user)
    pet = db_api.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


def update_pet(data: PetUpdate, current_user=Depends(get_current_user)):
    db_api = pet_crud.PetDatabaseApi(current_user)
    updated = db_api.update_pet(data)
    if not updated:
        raise HTTPException(status_code=404, detail="Pet not found")
    return updated


def delete_pet(pet_id: int, current_user=Depends(get_current_user)):
    db_api = pet_crud.PetDatabaseApi(current_user)
    deleted = db_api.delete_pet(pet_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pet not found")
    return {"detail": "Pet deleted successfully"}
