from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Portfolio

@receiver(post_save, sender=User)
def create_portfolio(sender, instance, created, **kwargs):
    if created:
        Portfolio.objects.create(owner=instance, cash=100000)