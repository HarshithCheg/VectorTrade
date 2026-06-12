from django.urls import path
from .views import BuyView, SellView, TransactionView, PortfolioView, PositionView

urlpatterns = [
    path('portfolio/', PortfolioView.as_view()),
    path('position/', PositionView.as_view()),
    path('trades/log/', TransactionView.as_view()),
    path('trades/buy/', BuyView.as_view()),
    path('trades/sell/', SellView.as_view()),
]