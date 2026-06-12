from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
ACTION_CHOICES = [("BUY", "Buy"), ("SELL", "Sell")]
class Portfolio(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    cash = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Position(models.Model):
    uid = models.UUIDField(default = uuid.uuid4, unique=True, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="positions")
    ticker = models.CharField(blank=False, null=False, max_length=10)
    qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=True)

class Trade(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="trades")
    ticker = models.CharField(blank=False, null=False, max_length=10)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
