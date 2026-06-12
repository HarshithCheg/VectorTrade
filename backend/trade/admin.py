from django.contrib import admin
from .models import Trade, Portfolio, Position

# Register your models here.
admin.site.register(Portfolio)
admin.site.register(Position)
admin.site.register(Trade)