from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    """
    Custom user model that extends the default Django user model.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_staff = models.BooleanField(default=False)  # Permite acceso al admin

    USERNAME_FIELD = 'email' # Use email to login
    REQUIRED_FIELDS = ['username'] # username is requiered for creating a user

    def __str__(self):
        return self.email
    
class Product(models.Model):
    """
    Model representing a product in the e-commerce system.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class Order(models.Model):
    """
    Model representing an order in the e-commerce system.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order {self.id} by {self.user.email}"
    
class OrderItem(models.Model):
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # if the product is deleted, we set it to null instead of deleting the order item
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    # Save the price at the time of purchase to avoid issues with price changes
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.title if self.product else 'Producto Eliminado'} in Order {self.order.id}"

    def save(self, *args, **kwargs):
        # If this is a new item or the price has not been set, take the current price of the product
        if not self.price_at_purchase and self.product:
            self.price_at_purchase = self.product.price
        super().save(*args, **kwargs)