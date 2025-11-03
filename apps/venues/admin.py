from django.contrib import admin, messages
from .models import Venue, VenueArea, SeatingPlan, Section, Seat, SectionType
from django import forms
from math import ceil


class VenueAreaInline(admin.TabularInline):
    model = VenueArea
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address", "pets_friendly")
    list_filter = ("city", "pets_friendly")
    search_fields = ("name", "city", "address")
    inlines = [VenueAreaInline]


class SeatingPlanInline(admin.TabularInline):
    model = SeatingPlan
    extra = 1


@admin.register(VenueArea)
class VenueAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "venue")
    list_filter = ("venue",)
    search_fields = ("name", "venue__name")
    inlines = [SeatingPlanInline]


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(SeatingPlan)
class SeatingPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "area")
    list_filter = ("area",)
    search_fields = ("title", "area__name", "area__venue__name")
    inlines = [SectionInline]


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 5


class GenerateSeatsForm(forms.Form):
    rows = forms.IntegerField(label="Liczba rzędów", min_value=1, initial=5)
    per_row = forms.IntegerField(
        label="Liczba miejsc w rzędzie", min_value=1, initial=10
    )


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "type", "capacity")
    list_filter = ("type", "plan__area__venue")
    search_fields = (
        "name",
        "plan__title",
        "plan__area__name",
        "plan__area__venue__name",
    )

    actions = ["auto_generate_seats"]

    def auto_generate_seats(self, request, queryset):
        total_created = 0

        for section in queryset:
            if section.type != SectionType.SEATED:
                continue

            capacity = section.capacity or 0
            if capacity <= 0:
                self.message_user(
                    request,
                    f"Sekcja {section.name}: brak ustawionej liczby miejsc.",
                    level=messages.WARNING,
                )
                continue

            if capacity <= 200:
                rows = 10
            elif capacity <= 1000:
                rows = 20
            elif capacity <= 5000:
                rows = 40
            else:
                rows = 60

            per_row = ceil(capacity / rows)

            seats_to_create = []
            for r in range(1, rows + 1):
                for n in range(1, per_row + 1):
                    if len(seats_to_create) >= capacity:
                        break
                    seats_to_create.append(
                        Seat(section=section, row=str(r), number=str(n))
                    )

            Seat.objects.bulk_create(seats_to_create)
            total_created += len(seats_to_create)

        self.message_user(
            request,
            f"Utworzono {total_created} miejsc.",
            level=messages.SUCCESS,
        )

    auto_generate_seats.short_description = (
        "Auto-generuj miejsca wg capacity (dynamicznie)"
    )


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("section", "row", "number", "is_wheelchair")
    list_filter = ("is_wheelchair", "section__plan__area__venue")
    search_fields = (
        "section__name",
        "row",
        "number",
        "section__plan__area__name",
        "section__plan__area__venue__name",
    )
