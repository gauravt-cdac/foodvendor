# admin.py
from django.contrib import admin
from .models import Cart

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'fooditem', 'quantity', 'updated_at']