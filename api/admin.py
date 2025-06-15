from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Product, Order, OrderItem

# Si usas CustomUser
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'is_staff'] # Campos que quieres ver en la lista
    # Si tienes campos personalizados en CustomUser, añádelos a fieldsets o add_fieldsets

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # Cuántos forms vacíos mostrar
    readonly_fields = ('price_at_purchase',) # El precio no se debería cambiar desde el admin una vez fijado

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
    readonly_fields = ('total_amount',) # El total se calcula automáticamente

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'stock_quantity', 'created_at')
    search_fields = ('title', 'description')

# Si usas CustomUser, registra tu CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin) # O UserAdmin si usas el User por defecto
# admin.site.register(Product) # Ya no es necesario si usas @admin.register
# admin.site.register(Order, OrderAdmin) # Ya no es necesario
# admin.site.register(OrderItem) # Generalmente se gestiona a través del OrderAdmin