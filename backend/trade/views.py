from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Portfolio, Position, Trade
from .serializers import PortfolioSerializer, TradeSerializer, PositionSerializer, LoginSerializer, RegisterSerializer, PredictSerializer, BackTestSerializer
from decimal import Decimal
from utils import load_model, BASE_DIR
from engine import Engine
from scipy.optimize import linprog
import pandas as pd
import numpy as np
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
# Create your views here.

class BuyView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        ticker = request.data.get("ticker")
        price = Decimal(request.data.get("price"))
        qty = Decimal(request.data.get("qty"))

        cost = price*qty
        user = self.request.user
        try:
            portfolio = Portfolio.objects.get(owner = user)
            if portfolio.cash < cost:
                raise ValueError("Insufficient Funds")
            position, created = Position.objects.get_or_create(
                portfolio= portfolio,
                ticker= ticker,
                defaults= {"qty" : 0, "avg_price": 0},
            )
            position.avg_price = (position.avg_price*position.qty + cost)/(qty + position.qty)
            position.qty += qty
            position.save()

            portfolio.cash -= cost
            portfolio.save()

            Trade.objects.create(
                portfolio= portfolio,
                ticker= ticker,
                action= "BUY",
                qty= qty,
                price= price,
            )
            return Response({"status" : "ok", "cash" : portfolio.cash}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Portfolio.DoesNotExist:
            return Response({"error": "Portfolio Not Found"}, status=status.HTTP_404_NOT_FOUND)

class SellView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        ticker = request.data.get("ticker")
        qty = Decimal(request.data.get("qty"))
        price = Decimal(request.data.get("price"))

        amt = price*qty
        user = self.request.user
        try:
            portfolio = Portfolio.objects.get(owner = user)
            position = Position.objects.get(portfolio = portfolio, ticker= ticker)
            if position.qty < qty:
                raise ValueError("Insufficient Shares")
            position.qty -= qty
            if position.qty == 0:
                position.delete()
            else:
                position.save()

            portfolio.cash += amt
            portfolio.save()

            Trade.objects.create(
                portfolio= portfolio,
                ticker= ticker,
                action= "SELL",
                qty= qty,
                price= price,
            )
            return Response({"status": "ok", "cash": portfolio.cash}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Portfolio.DoesNotExist:
            return Response({"error": "Portfolio Not Found"}, status=status.HTTP_404_NOT_FOUND)
        except Position.DoesNotExist:
            return Response({"error": "Position Not Found"}, status=status.HTTP_404_NOT_FOUND)

class TransactionView(ListAPIView):
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        portfolio = Portfolio.objects.get(owner= self.request.user)
        return Trade.objects.filter(portfolio= portfolio).order_by("-created_at")
    
class PortfolioView(RetrieveAPIView):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return Portfolio.objects.get(owner= self.request.user)
    
class PositionView(ListAPIView):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        portfolio = Portfolio.objects.get(owner= self.request.user)
        return Position.objects.filter(portfolio= portfolio)

class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer

class LogInView(APIView):
    def post(self, request):
        try:
            data = self.request.data
            serializer = LoginSerializer(data= data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access" : str(refresh.access_token),
                "uid" : str(user.uid),
                "username": str(user.username)
            })

        except Exception as e:
            raise ValidationError(e)
        
class LogOutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response({"status": "Log-Out Success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PredictView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            serializer = PredictSerializer(data= request.data)
            serializer.is_valid(raise_exception=True)
            ticker = serializer.validated_data["ticker"]
            model = load_model(ticker)
            df = pd.read_csv(BASE_DIR/f"data/pred/{ticker}_pred.csv")
            latest = df.iloc[-1]
            signal = ""
            if latest["Predicted"] == 1:
                signal = "BUY"
            else:
                signal = "SELL"
            return Response({
                "ticker": ticker,
                "date": latest["Date"],
                "signal": signal,
                "confidence": latest["Confidence"]
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class BackTestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            serializer = BackTestSerializer(data= request.data)
            serializer.is_valid(raise_exception=True)
            ticker = serializer.validated_data["ticker"]
            initCash = serializer.validated_data["initial_cash"]
            engine = Engine(initCash)
            load_model(ticker= ticker)
            pred_df = pd.read_csv(BASE_DIR/f"data/pred/{ticker}_pred.csv")
            price_df = pd.read_csv(BASE_DIR/f"data/price/{ticker}_price.csv")

            return Response(engine.backtest(pred_df= pred_df, price_df= price_df, ticker= ticker, qty= 10), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status= status.HTTP_400_BAD_REQUEST)

class PositionBacktest(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = self.request.user
            portfolio = Portfolio.objects.get(owner=user)
            positions = Position.objects.filter(portfolio=portfolio)
            if not positions.exists():
                return Response({"message": "No active positions found to optimize."}, status=status.HTTP_400_BAD_REQUEST)

            tickers = []
            prices = []
            util_scores = []
            bounds = []

            # Gather prediction values across user's portfolio
            for pos in positions:
                ticker = pos.ticker
                current_qty = float(pos.qty)

                load_model(ticker=ticker)
                pred_df = pd.read_csv(BASE_DIR / f"data/pred/{ticker}_pred.csv")
                price_df = pd.read_csv(BASE_DIR / f"data/price/{ticker}_price.csv")
                
                price_df["Date"] = pd.to_datetime(price_df["Date"])
                pred_df["Date"] = pd.to_datetime(pred_df["Date"])
                
                merged = pd.merge(price_df, pred_df, how="inner", on="Date").sort_values("Date")
                if merged.empty:
                    continue

                latest_day = merged.iloc[-1]
                price = float(latest_day["Close"])
                proba = float(latest_day["Confidence"])

                #Centered score around 0.5 (Scale: -0.5 to +0.5) => helps greatly with Linear Prog.
                scores = proba - 0.5

                tickers.append(ticker)
                prices.append(price)
                util_scores.append(scores)
                
                #Bounds mapping: Lower bound is -current_qty (cannot sell more than this), Upper bound is None (no strict upper bounds)
                bounds.append((-current_qty, None))

            if not tickers:
                return Response({"error": "No valid token data found"}, status=status.HTTP_400_BAD_REQUEST)

            # Optimization Part: Linear Prog.
            c = [-s for s in util_scores] # To maximize multiplying with -ve
            A_ub = [prices]
            b_ub = [float(portfolio.cash)]

            res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

            trades_executed = []
            failed_trades = []

            # Using existing Views via APIRequestFactory
            if res.success:
                factory = APIRequestFactory()

                # Keeping track of current position(i) and quantity(delta_qty)
                for i, delta_qty in enumerate(res.x):
                    ticker = tickers[i]
                    price = prices[i]
                    
                    trade_qty = round(delta_qty, 4)
                    if trade_qty == 0:
                        continue

                    trade_data = {
                        "ticker": ticker,
                        "price": str(price),
                        "qty": str(abs(trade_qty))
                    }

                    mock_http_req = factory.post(f'/api/trade/', trade_data, format='json')
                    drf_internal_request = Request(mock_http_req)
                    
                    # Passing along the pre-authenticated user profile to skip JWT decoding
                    drf_internal_request.user = user  # Bypasses authentication without the need of access tokens

                    # BuyViews
                    if trade_qty > 0:
                        try:
                            view_instance = BuyView.as_view()
                            response = view_instance(drf_internal_request)
                            
                            if response.status_code == status.HTTP_200_OK:
                                trades_executed.append({"ticker": ticker, "action": "BUY", "qty": trade_qty})
                            else:
                                failed_trades.append({"ticker": ticker, "action": "BUY", "error": response.data})
                        except Exception as e:
                            failed_trades.append({"ticker": ticker, "action": "BUY", "error": str(e)})

                    # SellViews
                    else:
                        try:
                            view_instance = SellView.as_view()
                            response = view_instance(drf_internal_request)
                            
                            if response.status_code == status.HTTP_200_OK:
                                trades_executed.append({"ticker": ticker, "action": "SELL", "qty": abs(trade_qty)})
                            else:
                                failed_trades.append({"ticker": ticker, "action": "SELL", "error": response.data})
                        except Exception as e:
                            failed_trades.append({"ticker": ticker, "action": "SELL", "error": str(e)})

                portfolio.refresh_from_db()
                return Response({
                    "status": "Optimization processing complete",
                    "trades_successful": trades_executed,
                    "trades_failed": failed_trades,
                    "remaining_cash": portfolio.cash
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": f"Optimization failed: {res.message}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
