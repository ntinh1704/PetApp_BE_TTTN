from fastapi import APIRouter, Depends
from controller import cart
from schemas.cart_schema import CartResponse, CartItemBase, CartItemUpdate
from setting.utils import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("", response_model=CartResponse)
def get_cart(_current_user=Depends(cart.get_user_cart)):
    return _current_user

@router.post("/add", response_model=CartResponse)
def add_to_cart(_current_user=Depends(cart.add_to_cart)):
    return _current_user

@router.put("/update", response_model=CartResponse)
def update_cart_item(_current_user=Depends(cart.update_cart_item)):
    return _current_user

@router.delete("/item", response_model=CartResponse)
def remove_from_cart(service_id: int, _current_user=Depends(get_current_user)):
    return cart.remove_from_cart(service_id, _current_user)

@router.delete("/clear", response_model=CartResponse)
def clear_cart(_current_user=Depends(cart.clear_cart)):
    return _current_user
