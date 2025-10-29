from django.db import models


class Payment(models.Model):
    class Provider(models.TextChoices):
        DUMMY = "dummy", "Dummy"
        P24 = "p24", "P24"
        PAYU = "payu", "Payu"
        BLIK = "blik", "Blik"

    class Status(models.TextChoices):
        CREATED = "created", "Utworzona"
        PENDING = "pending", "Oczekująca"
        AUTHORIZED = "authorized", "Autoryzowana"
        SUCCEEDED = "succeeded", "Zakończona pomyślnie"
        FAILED = "failed", "Nieudana"
        CANCELED = "canceled", "Anulowana"

    booking = models.OneToOneField(
        "booking.Booking",
        on_delete=models.CASCADE,
        related_name="payment",
        null=True,
        blank=True,
    )

    amount = models.DecimalField(decimal_places=2, max_digits=10)
    currency = models.CharField(max_length=3, default="PLN")
    description = models.CharField(max_length=255, null=True, blank=True)

    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.DUMMY
    )
    external_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="External ID for this payment"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True
    )

    payer_email = models.EmailField(blank=True)
    metadata = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["provider", "external_id"]),
        ]
        verbose_name = "Płatność"
        verbose_name_plural = "Płatności"

    def __str__(self):
        return f"Payment#{self.pk} {self.amount} {self.currency} [{self.status}]"

    @property
    def is_final(self) -> bool:
        return self.status in {
            self.Status.SUCCEEDED,
            self.Status.CANCELED,
            self.Status.FAILED,
        }
