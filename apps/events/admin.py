from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "date",
        "city",
        "venue",
        "price",
        "total_seats",
        "available_seats",
    )
    list_filter = ("city", "date")
    search_fields = ("name", "venue", "city")
    ordering = ("date",)
    list_editable = ("available_seats", "price")
    readonly_fields = ("id",)

    fieldsets = (
        ("Podstawowe informacje", {
            "fields": ("name", "date", "city", "venue")
        }),
        ("Bilety", {
            "fields": ("total_seats", "available_seats", "price")
        }),
        ("Opis", {
            "fields": ("description", "highlights")
        }),
    )
