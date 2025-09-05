from django.conf import settings
from django.db import models

class Booking(models.Model):
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    ticket_number = models.CharField(max_length=32, unique=True)
    pdf_file = models.FileField(upload_to='tickets/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.ticket_number} – {self.full_name}'
