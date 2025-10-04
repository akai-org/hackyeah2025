"""
Modele podstawowe: Przewoźnicy i typy stacji
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Carrier(models.Model):
    """Model representing a public transport carrier"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Carrier name")
    priority = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Carrier priority (0-10, where 10 is highest)"
    )
    ticket_purchase_link = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ticket purchase link"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrier"
        verbose_name_plural = "Carriers"
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.name} (priority: {self.priority})"


class StationType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, verbose_name="Station type name")

    class Meta:
        verbose_name = "Station type"
        verbose_name_plural = "Station types"

    def __str__(self):
        return self.name

