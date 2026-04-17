from sqlalchemy.orm import Session
from fastapi import HTTPException
from db import models
from schemas.cart_schema import CartItemBase, CartItemUpdate

class CartDatabaseApi:
    def __init__(self, current_user):
        db, token_data, _ = current_user
        self.db: Session = db
        self.user = token_data

    def _current_uid(self):
        if isinstance(self.user, dict):
            return self.user.get("id") or self.user.get("user_id")
        return getattr(self.user, "id", None) or getattr(self.user, "user_id", None)

    def get_user_cart(self):
        current_uid = self._current_uid()
        if not current_uid:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = self.db.query(models.Cart).filter(models.Cart.user_id == current_uid).first()
        if not cart:
            cart = models.Cart(user_id=current_uid)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        
        return cart

    def add_to_cart(self, item_data: CartItemBase):
        cart = self.get_user_cart()
        
        # Check if item already exists
        existing_item = self.db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.service_id == item_data.service_id
        ).first()

        if existing_item:
            existing_item.quantity += item_data.quantity
        else:
            new_item = models.CartItem(
                cart_id=cart.id,
                service_id=item_data.service_id,
                quantity=item_data.quantity
            )
            self.db.add(new_item)
        
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def update_cart_item(self, item_data: CartItemUpdate):
        cart = self.get_user_cart()
        
        item = self.db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.service_id == item_data.service_id
        ).first()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found in cart")

        if item_data.quantity <= 0:
            self.db.delete(item)
        else:
            item.quantity = item_data.quantity
        
        self.db.commit()
        self.db.refresh(cart)
        return cart

    def remove_from_cart(self, service_id: int):
        cart = self.get_user_cart()
        
        item = self.db.query(models.CartItem).filter(
            models.CartItem.cart_id == cart.id,
            models.CartItem.service_id == service_id
        ).first()

        if item:
            self.db.delete(item)
            self.db.commit()
            self.db.refresh(cart)
        
        return cart

    def clear_cart(self):
        cart = self.get_user_cart()
        self.db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
        self.db.commit()
        self.db.refresh(cart)
        return cart
