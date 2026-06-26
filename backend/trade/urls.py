from django.urls import path
from .views import BuyView, SellView, TransactionView, PortfolioView, PositionView, LatestPriceView
from .views import LogInView, LogOutView, RegisterView, PredictView, BackTestView, PortfolioAllocator
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('portfolio/', PortfolioView.as_view()),
    path('position/', PositionView.as_view()),
    path('portfolio/allocation', PortfolioAllocator.as_view()),
    path('trades/log/', TransactionView.as_view()),
    path('trades/buy/', BuyView.as_view()),
    path('trades/sell/', SellView.as_view()),
    path('login/', LogInView.as_view()),
    path('logout/', LogOutView.as_view()),
    path('predict/', PredictView.as_view()),
    path('backtest/', BackTestView.as_view()),
    path('price/latest/', LatestPriceView.as_view()),
]