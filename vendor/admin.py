from django.contrib import admin
from vendor.models import Vendor
from .models import OpeningHour


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('user', 'vendor_name', 'is_approved', 'created_at')
    list_display_links = ('user', 'vendor_name')
    list_editable = ('is_approved',)
    search_fields = ('vendor_name', 'user__username')
    list_filter = ('is_approved', 'created_at')


@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'day', 'from_hour', 'to_hour', 'is_closed')
    list_filter = ('vendor', 'day', 'is_closed')
    search_fields = ('vendor__vendor_name',)
