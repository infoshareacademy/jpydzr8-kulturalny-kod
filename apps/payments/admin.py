from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "amount", "currency", "provider", "status", "created_at")
    list_filter = ("provider", "status", "currency", "created_at")
    search_fields = ("id", "external_id", "description", "payer_email")
    readonly_fields = ("created_at", "updated_at")
