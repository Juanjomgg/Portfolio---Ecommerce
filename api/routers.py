from typing import List
from django.shortcuts import get_object_or_404
from django.db import transaction
from ninja import Router
from ninja.responses import Response
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Product, Order, OrderItem, CustomUser
from .schemas import (
    ProductSchema, ProductCreateSchema,
    OrderSchema, OrderCreateSchema, OrderItemCreateSchema,
    UserSchema, UserCreateSchema,
    TokenSchema, TokenRequest, RefreshTokenSchema, ErrorMessageSchema,
    PublicKeySchema, EncryptedTokenRequest
)
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from functools import wraps
import time
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import unpad
# Cambiamos a PKCS1_v1_5 para compatibilidad con JSEncrypt
from Crypto.Cipher import PKCS1_v1_5
import base64
import os
# Intentar descifrar con un centinela aleatorio
from os import urandom



# ----- Routers -----
product_router = Router(tags=["Products"], auth=JWTAuth())  # Protected routes except list and get
user_router = Router(tags=["Users"])
order_router = Router(tags=["Orders"], auth=JWTAuth())  # All order routes are protected

# Rate limiting decorator
def rate_limit(key_prefix, limit=5, period=60):
    """
    Rate limiting decorator
    :param key_prefix: Prefix for the cache key
    :param limit: Number of allowed requests per period
    :param period: Time period in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Obtener IP del cliente
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            if ip:
                # Tomar solo la primera IP si hay varias
                ip = ip.split(',')[0].strip()
                # Reemplazar caracteres no válidos para memcached
                ip = ip.replace(' ', '_').replace(':', '_')
            else:
                ip = 'unknown'
            
            key = f"rl_{key_prefix}_{ip}"  # Formato seguro para memcached
            
            # Obtener las solicitudes recientes del caché
            requests = cache.get(key, [])
            now = time.time()
            
            # Limpiar solicitudes antiguas
            requests = [req for req in requests if req > now - period]
            
            if len(requests) >= limit:
                return {"detail": "Too many requests"}, 429
            
            # Agregar la solicitud actual
            requests.append(now)
            cache.set(key, requests, period)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


# Generar par de claves RSA si no existe
KEY_PATH = os.path.join(os.path.dirname(__file__), 'private_key.pem')
if not os.path.exists(KEY_PATH):
    key = RSA.generate(2048)
    with open(KEY_PATH, 'wb') as f:
        f.write(key.export_key('PEM'))
else:
    with open(KEY_PATH, 'rb') as f:
        key = RSA.import_key(f.read())

@user_router.get("/public-key", response=PublicKeySchema, auth=None)
def get_public_key(request):
    """Retorna la clave pública RSA en formato PEM"""
    public_key = key.publickey().export_key('PEM').decode()
    return PublicKeySchema(key=public_key)


@user_router.post("/token", response=TokenSchema|ErrorMessageSchema, auth=None)
@rate_limit("login", limit=5, period=300)  # 5 intentos cada 5 minutos
def obtain_token(request, data: EncryptedTokenRequest):
    if not data.encrypted_password:
        return ErrorMessageSchema(detail="No password provided")

    try:
        # Intentar decodificar el base64
        try:
            encrypted_bytes = base64.b64decode(data.encrypted_password)
        except Exception as e:
            return ErrorMessageSchema(detail="Invalid password format")

        # Verificar que tenemos la clave privada correcta
        # Usar PKCS1_v1_5 para compatibilidad con JSEncrypt
        cipher = PKCS1_v1_5.new(key)
        
        sentinel = urandom(32)  # Usar un centinela aleatorio
        password_bytes = cipher.decrypt(encrypted_bytes, sentinel)
        
        if password_bytes == sentinel:
            raise ValueError("Decryption failed - got sentinel value")
        
        # Intentar decodificar como UTF-8
        password = password_bytes.decode('utf-8')
        
        if not password:
            return ErrorMessageSchema(detail="Empty password after decryption")
            
        # Autenticar usuario
        user = authenticate(email=data.email, password=password)
        if user is None:
            return ErrorMessageSchema(detail="Invalid credentials")

        refresh = RefreshToken.for_user(user)
        # Crear una respuesta personalizada con Response de ninja
        response = Response(
            {"access": str(refresh.access_token)},
            status=200
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=7 * 24 * 60 * 60,
            path="/api/users/token/refresh"
        )
        return response
        
    except ValueError as e:
        return ErrorMessageSchema(detail="Invalid encrypted data - decryption failed")
    except Exception as e:
        return ErrorMessageSchema(detail="Decryption error")

@user_router.post("/token/refresh", response=TokenSchema, auth=None)
def refresh_token(request):
    try:
        refresh_token_cookie = request.COOKIES.get('refresh_token')
        if not refresh_token_cookie:
            return {"detail": "No refresh token cookie"}, 401
            
        refresh_token = RefreshToken(refresh_token_cookie)
        response = Response(
            {"access": str(refresh_token.access_token)},
            status=200
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh_token),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
            path="/api/users/token/refresh"
        )
        return response
    except Exception as e:
        return {"detail": "Invalid refresh token"}, 401

@user_router.post("/register", response=UserSchema, summary="Register a new user", auth=None)
def register_user(request, payload: UserCreateSchema):
    if CustomUser.objects.filter(email=payload.email).exists():
        return {"detail": "Email already registered"}, 400

    user = CustomUser.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name or "",
        last_name=payload.last_name or ""
    )
    return user

@product_router.get("/", response=List[ProductSchema], summary="List all products", auth=None)
def list_products(request):
    return Product.objects.all()

@product_router.get("/{product_id}", response=ProductSchema, summary="Get a specific product", auth=None)
def get_product(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    return product

@product_router.post("/", response=ProductSchema, summary="Create a new product (admin/staff only)")
def create_product(request, payload: ProductCreateSchema):
    if not request.auth or not request.auth.is_staff:
        return {"detail": "You do not have permission to perform this action"}, 403
    product = Product.objects.create(**payload.dict())
    return product

# --- Endpoints de Pedidos (Protegidos por AuthBearer) ---
@order_router.post("/", response=OrderSchema, summary="Create a new order")
@transaction.atomic # Asegura que todas las operaciones de DB se completen o ninguna
def create_order(request, payload: OrderCreateSchema):
    user = request.auth # El usuario autenticado por JWT
    if not user or not user.is_authenticated:
        return {"detail": "Authentication required"}, 401
    if not payload.items:
        return {"detail": "Order must contain at least one item"}, 400

    order = Order.objects.create(user=user, status='PENDING')
    total_order_amount = 0

    for item_data in payload.items:
        try:
            product = Product.objects.select_for_update().get(id=item_data.product_id) # Bloquear producto para evitar race conditions
        except Product.DoesNotExist:
            # Si un producto no existe, se puede cancelar toda la orden o ignorar el item.
            # No debería de pasar ya que el frontend envia solo productos válidos recuperados de la API
            #transaction.set_rollback(True) # Marcar para rollback
            return {"detail": f"Product with id {item_data.product_id} not found"}, 404
        if product.stock_quantity < item_data.quantity:
            transaction.set_rollback(True)
            return {"detail": f"Not enough stock for {product.title}. Available: {product.stock_quantity}"}, 400

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item_data.quantity,
            price_at_purchase=product.price # Guardamos el precio actual
        )
        
        total_order_amount += order_item.price_at_purchase * order_item.quantity
        product.stock_quantity -= item_data.quantity
        product.save()

    order.total_amount = total_order_amount
    order.save()
    return order


@order_router.get("/", response=List[OrderSchema], summary="List user's orders")
def list_orders(request):
    user = request.auth
    if not user or not user.is_authenticated:
        return {"detail": "Authentication required"}, 401
    # Usamos prefetch_related para optimizar y traer los items y productos relacionados en menos queries
    orders = Order.objects.filter(user=user).prefetch_related('items__product', 'user').all()
    return orders

@order_router.get("/{order_id}", response=OrderSchema, summary="Get a specific order")
def get_order(request, order_id: int):
    user = request.auth
    if not user or not user.is_authenticated:
        return {"detail": "Authentication required"}, 401

    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'user'),
        id=order_id,
        user=user # Asegura que el usuario solo pueda ver sus propios pedidos
    )
    return order
