from rest_framework import serializers
from .models import Portfolio, Position, Trade

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('uid', 'cash', 'owner', 'created_at',)
        read_only_fields = ('owner', 'created_at',)

class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('uid', 'portfolio', 'ticker', 'qty', 'avg_price',)

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = ('uid', 'portfolio', 'ticker', 'action', 'qty', 'price', 'created_at',)
        read_only_fields = ('created_at',)