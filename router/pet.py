from fastapi import APIRouter, Depends

from controller import pet
from schemas.pet_schema import PetBase, PetCreate, PetUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.get("")
def get_list_pet(
    data=Depends(pet.get_list_pet),
):
    return data


@router.get("/{pet_id}", response_model=PetBase)
def get_pet_by_id(
    pet_id: int,
    _current_user=Depends(get_current_user),
):
    return pet.get_pet_by_id(pet_id, _current_user)


@router.post("/", response_model=PetBase)
def create_pet(
    data: PetCreate,
    _current_user=Depends(get_current_user),
):
    return pet.create_pet(data, _current_user)


@router.put("/", response_model=PetBase)
def update_pet(
    data: PetUpdate,
    _current_user=Depends(get_current_user),
):
    return pet.update_pet(data, _current_user)


@router.delete("/")
def delete_pet(
    pet_id: int,
    _current_user=Depends(get_current_user),
):
    return pet.delete_pet(pet_id, _current_user)
