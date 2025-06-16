from ninja import Schema, ModelSchema
from typing import List, Optional
from datetime import datetime
from .models import Product, Order, OrderItem, CustomUser # o from django.contrib.auth.models import User

# Schemas de Usuario
class UserSchema(ModelSchema):
    class Config:
        model = CustomUser # o User
        model_fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserCreateSchema(Schema): # Para creación, solo necesitamos lo esencial y la contraseña
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Schemas de Producto
class ProductSchema(ModelSchema):
    class Config:
        model = Product
        model_fields = ['id', 'title', 'description', 'price', 'stock_quantity']  # Incluimos explícitamente stock_quantity

class ProductCreateSchema(ModelSchema): # Para creación, no necesitamos id, created_at, updated_at
    class Config:
        model = Product
        model_fields = ['title', 'description', 'price', 'stock_quantity']

# Schemas de OrderItem
class OrderItemSchema(ModelSchema):
    product: ProductSchema # Mostrar el producto completo anidado

    class Config:
        model = OrderItem
        model_fields = ['id', 'product', 'quantity', 'price_at_purchase']

class OrderItemCreateSchema(Schema): # Para crear un item dentro de un pedido
    product_id: int
    quantity: int

# Schemas de Pedido
class OrderSchema(ModelSchema):
    user: UserSchema
    items: List[OrderItemSchema] = None  # Inicializar como None

    @staticmethod
    def resolve_items(obj):
        return obj.orderitem_set.all()  # Obtener todos los items relacionados

    class Config:
        model = Order
        model_fields = ['id', 'user', 'created_at', 'status', 'total_amount']

class OrderCreateSchema(Schema):
    items: List[OrderItemCreateSchema]
    # El usuario se tomará del usuario autenticado
    # El status y total_amount se calcularán

# Schemas de Autenticación
class TokenRequest(Schema):
    email: str
    password: str

class TokenSchema(Schema):
    access: str  # Solo devolvemos el access token

class RefreshTokenSchema(Schema):
    refresh: str

# Schema para mensajes de error
class ErrorMessageSchema(Schema):
    detail: str