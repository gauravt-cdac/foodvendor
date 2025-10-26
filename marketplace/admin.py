from django.contrib import admin
from .models import Cart, Tax


class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'fooditem', 'quantity', 'updated_at')


class TaxAdmin(admin.ModelAdmin):
    list_display = ('tax_type', 'tax_percentage', 'is_active')


# ✅ Keep all registrations together at the end
admin.site.register(Tax, TaxAdmin)
admin.site.register(Cart, CartAdmin)
