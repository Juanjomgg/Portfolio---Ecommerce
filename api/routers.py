from typing import List
from django.shortcuts import get_object_or_404
from django.db import transaction
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Product, Order, OrderItem, CustomUser
from .schemas import (
    ProductSchema, ProductCreateSchema,
    OrderSchema, OrderCreateSchema, OrderItemCreateSchema,
    UserSchema, UserCreateSchema,
    TokenSchema, TokenRequest, RefreshTokenSchema, ErrorMessageSchema
)

# ----- Routers -----
product_router = Router(tags=["Products"], auth=JWTAuth())  # Protected routes except list and get
user_router = Router(tags=["Users"])
order_router = Router(tags=["Orders"], auth=JWTAuth())  # All order routes are protected

# Añadir los endpoints de JWT
@user_router.post("/token", response=TokenSchema|ErrorMessageSchema, auth=None)
def obtain_token(request, data: TokenRequest):
    print("[DEBUG] Payload recibido en /token:", data)
    user = authenticate(email=data.email, password=data.password)  # Usar email como campo de login
    if user is None:
        return ErrorMessageSchema(detail="Invalid credentials")

    refresh = RefreshToken.for_user(user)
    values = {}
    values['access'] = str(refresh.access_token)
    values['refresh'] = str(refresh)
    return TokenSchema(**values)

@user_router.post("/token/refresh", response=TokenSchema, auth=None)
def refresh_token(request, data: RefreshTokenSchema):
    try:
        refresh_token = RefreshToken(data.refresh)
        return TokenSchema(
            access=str(refresh_token.access_token),
            refresh=str(refresh_token)
        )
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

# Más endpoints (PUT/DELETE para productos si eres admin, cambiar estado de orden, etc.) pueden añadirse.