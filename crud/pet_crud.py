from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from schemas.pet_schema import PetCreate, PetUpdate


class PetDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data

    def get_list_pet(self, offset: int = 0, limit: int = 10, text_search: str = None):
        # Lấy current user
        current_uid = (
            self.user.get("user_id")
            if isinstance(self.user, dict)
            else getattr(self.user, "user_id", None)
        )
        current_role = (
            self.user.get("role")
            if isinstance(self.user, dict)
            else getattr(self.user, "role", None)
        )

        query = self.db.query(models.Pet)

        # Chỉ thấy pet của mình nếu không phải admin
        if current_role != "admin" and current_uid is not None:
            query = query.filter(models.Pet.user_id == current_uid)

        if text_search:
            query = query.filter(models.Pet.name.ilike(f"%{text_search}%"))

        total = query.count()
        pets = query.offset(offset).limit(limit).all()

        data = [
            {
                "id": p.id,
                "user_id": p.user_id,
                "name": p.name,
                "breed": p.breed,
                "gender": p.gender,
                "age": p.age,
                "color": p.color,
                "height": p.height,
                "weight": p.weight,
                "image": p.image,
                "created_at": p.created_at,
            }
            for p in pets
        ]
        return data, total

    def get_pet_by_id(self, pet_id: int):
        current_uid = (
            self.user.get("user_id")
            if isinstance(self.user, dict)
            else getattr(self.user, "user_id", None)
        )
        current_role = (
            self.user.get("role")
            if isinstance(self.user, dict)
            else getattr(self.user, "role", None)
        )

        query = self.db.query(models.Pet).filter(models.Pet.id == pet_id)
        if current_role != "admin" and current_uid is not None:
            query = query.filter(models.Pet.user_id == current_uid)
        return query.first()

    def create_pet(self, data: PetCreate):
        current_uid = (
            self.user.get("user_id")
            if isinstance(self.user, dict)
            else getattr(self.user, "user_id", None)
        )
        new_pet = models.Pet(
            user_id=current_uid,
            name=data.name,
            breed=data.breed,
            gender=data.gender,
            age=data.age,
            color=data.color,
            height=data.height,
            weight=data.weight,
            image=data.image,
        )

        self.db.add(new_pet)
        self.db.commit()
        self.db.refresh(new_pet)
        return new_pet

    def update_pet(self, data: PetUpdate):

        pet = self.db.query(models.Pet).filter(models.Pet.id == data.id).first()
        if not pet:
            return None

        current_uid = (
            self.user.get("user_id")
            if isinstance(self.user, dict)
            else getattr(self.user, "user_id", None)
        )
        current_role = (
            self.user.get("role")
            if isinstance(self.user, dict)
            else getattr(self.user, "role", None)
        )

        if (
            current_role != "admin"
            and current_uid is not None
            and pet.user_id != current_uid
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to update this pet"
            )

        if data.name is not None:
            pet.name = data.name
        if data.breed is not None:
            pet.breed = data.breed
        if data.gender is not None:
            pet.gender = data.gender
        if data.age is not None:
            pet.age = data.age
        if data.color is not None:
            pet.color = data.color
        if data.height is not None:
            pet.height = data.height
        if data.weight is not None:
            pet.weight = data.weight
        if data.image is not None:
            pet.image = data.image

        self.db.commit()
        self.db.refresh(pet)
        return pet

    def delete_pet(self, pet_id: int):
        pet = self.db.query(models.Pet).filter(models.Pet.id == pet_id).first()
        if not pet:
            return None

        current_uid = (
            self.user.get("user_id")
            if isinstance(self.user, dict)
            else getattr(self.user, "user_id", None)
        )
        current_role = (
            self.user.get("role")
            if isinstance(self.user, dict)
            else getattr(self.user, "role", None)
        )

        if (
            current_role != "admin"
            and current_uid is not None
            and pet.user_id != current_uid
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this pet"
            )

        self.db.delete(pet)
        self.db.commit()
        return pet
