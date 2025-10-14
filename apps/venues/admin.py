from django.contrib import admin
from .models import Venue, VenueArea, SeatingPlan, Section, Seat


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "pets_friendly")
    list_filter = ("city", "pets_friendly")
    search_fields = ("name", "city", "address")


@admin.register(VenueArea)
class VenueAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "venue")
    list_filter = ("venue",)
    # było: ("name", "venue_name")
    search_fields = ("name", "venue__name")


@admin.register(SeatingPlan)
class SeatingPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "area")
    list_filter = ("area",)
    # było: ("title", "area_name")
    search_fields = ("title", "area__name", "area__venue__name")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "type", "capacity")
    # było: ("type", "plan_area_venue")
    list_filter = ("type", "plan__area__venue")
    # było: ("name", "plan_title", "plan_area_venue_name")
    search_fields = ("name", "plan__title", "plan__area__name", "plan__area__venue__name")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("section", "row", "number", "is_wheelchair")
    # było: ("is_wheelchair", "section_plan_area_venue")
    list_filter = ("is_wheelchair", "section__plan__area__venue")
    # było: ("section_name", "row", "number")
    search_fields = ("section__name", "row", "number",
                     "section__plan__area__name", "section__plan__area__venue__name")
