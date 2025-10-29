from django.db import models


class SectionType(models.TextChoices):
    SEATED = "seated", "Miejsca siedzące"
    STANDING = "standing", "Miejsca stojące"


class Venue(models.Model):
    name = models.CharField("Nazwa obiektu", max_length=200)
    city = models.CharField("Miejscowość", max_length=100)
    address = models.CharField("Adres", max_length=200, blank=True)
    pets_friendly = models.BooleanField("Wstęp ze zwierzętami", default=False)
    description = models.TextField("Opis", blank=True)

    class Meta:
        verbose_name = "Obiekt"
        verbose_name_plural = "Obiekty"

    def __str__(self):
        return f"{self.name} ({self.city})"


class VenueArea(models.Model):
    # Sala / obszar obiektu, w którym odbywa się wydarzenie
    venue = models.ForeignKey(
        "Venue",
        on_delete=models.CASCADE,
        related_name="areas",
        verbose_name="Obiekt",
    )
    name = models.CharField("Nazwa sali / obszaru", max_length=120)

    class Meta:
        verbose_name = "Sala / obszar obiektu"
        verbose_name_plural = "Sale / obszary obiektu"
        constraints = [
            models.UniqueConstraint(
                fields=["venue", "name"],
                name="uniq_venuearea_per_venue_name",
            ),
        ]

    def __str__(self):
        return f"{self.venue.name} — {self.name}"


class SeatingPlan(models.Model):
    # Schemat sali/obszaru i układ miejsc dla VenueArea
    area = models.ForeignKey(
        "VenueArea",
        on_delete=models.CASCADE,
        related_name="plans",
        verbose_name="Sala / obszar obiektu",
    )
    title = models.CharField("Układ miejsc", max_length=120)

    class Meta:
        verbose_name = "Układ miejsc"
        verbose_name_plural = "Układy miejsc"
        constraints = [
            models.UniqueConstraint(
                fields=["area", "title"],
                name="uniq_seatingplan_per_area_title",
            ),
        ]

    def __str__(self):
        return f"{self.area} — {self.title}"


class Section(models.Model):
    plan = models.ForeignKey(
        "SeatingPlan",
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Plan",
    )
    name = models.CharField("Nazwa sektora", max_length=80)
    type = models.CharField(
        "Typ sektora",
        max_length=10,
        choices=SectionType.choices,
        default=SectionType.SEATED,
    )

    capacity = models.PositiveIntegerField(
        "Maksymalna liczba miejsc",
        default=0,
        help_text="Dotyczy miejsc stojących.",
    )
    price_modifier = models.DecimalField(
        "Dopłata do ceny bazowej",
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="VIP +150, Balkon +60, Płyta 0",
    )

    class Meta:
        verbose_name = "Sektor"
        verbose_name_plural = "Sektory"
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "name"],
                name="uniq_section_per_plan_name",
            ),
        ]

    def is_seated(self) -> bool:
        return self.type == SectionType.SEATED

    def __str__(self):
        return f"{self.plan} — {self.name}"


class Seat(models.Model):
    # Pojedyncze miejsce w sektorze siedzącym
    section = models.ForeignKey(
        "Section",
        on_delete=models.CASCADE,
        related_name="seats",
        verbose_name="Sektor",
    )
    row = models.CharField("Rząd", max_length=10)
    number = models.CharField("Numer", max_length=10)
    is_wheelchair = models.BooleanField("Miejsce dla osoby na wózku", default=False)

    class Meta:
        verbose_name = "Miejsce"
        verbose_name_plural = "Miejsca"
        constraints = [
            models.UniqueConstraint(
                fields=["section", "row", "number"],
                name="uniq_seat_per_section_row_number",
            ),
        ]

    def __str__(self):
        return f"{self.section.name} R{self.row} #{self.number}"
