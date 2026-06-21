# services.py
from decimal import Decimal
from .models import Portfolio, Position, Trade

def execute_buy(user, ticker, price, qty):
    price = Decimal(str(price))
    qty = Decimal(str(qty))
    cost = price * qty

    portfolio = Portfolio.objects.get(owner=user)
    if portfolio.cash < cost:
        raise ValueError("Insufficient Funds")

    position, _ = Position.objects.get_or_create(
        portfolio=portfolio,
        ticker=ticker,
        defaults={"qty": 0, "avg_price": 0},
    )
    position.avg_price = (position.avg_price * position.qty + cost) / (qty + position.qty)
    position.qty += qty
    position.save()

    portfolio.cash -= cost
    portfolio.save()

    Trade.objects.create(portfolio=portfolio, ticker=ticker, action="BUY", qty=qty, price=price)

def execute_sell(user, ticker, price, qty):
    price = Decimal(str(price))
    qty = Decimal(str(qty))
    amt = price * qty

    portfolio = Portfolio.objects.get(owner=user)
    position = Position.objects.get(portfolio=portfolio, ticker=ticker)

    if position.qty < qty:
        raise ValueError("Insufficient Shares")

    position.qty -= qty
    if position.qty == 0:
        position.delete()
    else:
        position.save()

    portfolio.cash += amt
    portfolio.save()

    Trade.objects.create(portfolio=portfolio, ticker=ticker, action="SELL", qty=qty, price=price)