from django.db import models

class Event(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    city = models.CharField(max_length=255, default="")
    venue = models.CharField(max_length=255)
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)
    highlights = models.JSONField(blank=True, null=True)
    def __str__(self):
        return f"{self.name} - {self.date.strftime('%Y-%m-%d')}"
