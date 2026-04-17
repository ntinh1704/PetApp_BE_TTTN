from fastapi import Depends, HTTPException
from crud import cart_crud
from schemas.cart_schema import CartItemBase, CartItemUpdate
from setting.utils import get_current_user

def get_user_cart(current_user=Depends(get_current_user)):
    db_api = cart_crud.CartDatabaseApi(current_user)
    return db_api.get_user_cart()

def add_to_cart(data: CartItemBase, current_user=Depends(get_current_user)):
    db_api = cart_crud.CartDatabaseApi(current_user)
    return db_api.add_to_cart(data)

def update_cart_item(data: CartItemUpdate, current_user=Depends(get_current_user)):
    db_api = cart_crud.CartDatabaseApi(current_user)
    return db_api.update_cart_item(data)

def remove_from_cart(service_id: int, current_user=Depends(get_current_user)):
    db_api = cart_crud.CartDatabaseApi(current_user)
    return db_api.remove_from_cart(service_id)

def clear_cart(current_user=Depends(get_current_user)):
    db_api = cart_crud.CartDatabaseApi(current_user)
    return db_api.clear_cart()
