from django.contrib import admin
from .models import Booking, BookingItem


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        # "event",
        "user",
        # "full_name",
        "email",
        # "quantity",
        "total_price",
        # "ticket_number",
        # "created_at",
    )
    # list_filter = ("event", "created_at", "user")
    # search_fields = ("full_name", "email", "ticket_number")
    # ordering = ("-created_at",)
    # readonly_fields = ("created_at", "ticket_number", "total_price")
    # fieldsets = (
    #     (None, {
    #         "fields": ("event", "user", "full_name", "email", "quantity")
    #     }),
    #     ("Szczegóły biletu", {
    #         "fields": ("ticket_number", "pdf_file", "total_price")
    #     }),
    #     ("Systemowe", {
    #         "fields": ("created_at",),
    #     }),
    # )
