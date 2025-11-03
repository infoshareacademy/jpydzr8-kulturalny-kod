from django.db import models
from apps.venues.models import SeatingPlan, VenueArea, Venue


class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    city = models.CharField(max_length=255, default="")
    venue_area = models.ForeignKey(
        VenueArea,
        on_delete=models.PROTECT,
        related_name="events",
        null=True,
        blank=True,
    )
    seating_plan = models.ForeignKey(
        SeatingPlan,
        on_delete=models.PROTECT,
        related_name="events",
        null=True,
        blank=True,
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Obiekt",
        null=True,
        blank=True
    )
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    highlights = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.date.strftime('%Y-%m-%d')}"


class EventSeat(models.Model):
    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="event_seats"
    )
    seat = models.ForeignKey(
        "venues.Seat",
        on_delete=models.PROTECT,
        related_name="event_seats",
        null=True,
        blank=True
    )
    section = models.ForeignKey(
        "venues.Section",
        on_delete=models.PROTECT,
        related_name="event_seats",
        null=True,
        blank=True
    )

    is_reserved = models.BooleanField(default=False)
    reserved_at = models.DateTimeField(null=True, blank=True)

    @property
    def section(self):
        return self.seat.section if self.seat else None

    @property
    def is_standing(self):
        return not self.seat  # brak seat = stojące

    class Meta:
        unique_together = ("event", "seat")
        indexes = [
            models.Index(fields=["event", "is_reserved"]),
        ]

    def __str__(self):
        if self.seat:
            return f"{self.event.name} :: {self.seat.section.name} R{self.seat.row} #{self.seat.number}"
        return f"{self.event.name} :: {self.section.name} (standing)"
