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
from .services import execute_buy, execute_sell
# Create your views here.

class BuyView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        ticker = request.data.get("ticker")
        price = Decimal(request.data.get("price"))
        qty = Decimal(request.data.get("qty"))
        user = self.request.user
        try:
            portfolio = Portfolio.objects.get(owner=user)
            execute_buy(user=user, ticker=ticker, price= price, qty= qty)
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
            portfolio = Portfolio.objects.get(owner= user)
            execute_sell(user= user, ticker= ticker, price= price, qty= qty)
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

class RegisterView(APIView):
    def post(self, request):
        data = self.request.data
        serializer = RegisterSerializer(data= data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "uid": str(user.uid),
            "username": str(user.username),
        }, status= status.HTTP_201_CREATED)

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

            return Response(engine.backtest(pred_df= pred_df, price_df= price_df, ticker= ticker), status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status= status.HTTP_400_BAD_REQUEST)

class PortfolioAllocator(APIView):
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
            current_qtys = []

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
                scores = proba - 0.5

                tickers.append(ticker)
                prices.append(price)
                util_scores.append(scores)
                current_qtys.append(current_qty)

            if not tickers:
                return Response({"error": "No valid ticker data found"}, status=status.HTTP_400_BAD_REQUEST)

            trades_executed = []
            failed_trades = []

            # PHASE 1 — Execute all SELLS first for negative-confidence positions
            for i, ticker in enumerate(tickers):
                if util_scores[i] < 0 and current_qtys[i] > 0:
                    try:
                        execute_sell(user, ticker, prices[i], current_qtys[i])
                        trades_executed.append({"ticker": ticker, "action": "SELL", "qty": current_qtys[i]})
                        current_qtys[i] = 0  # now sold, qty is 0
                    except Exception as e:
                        failed_trades.append({"ticker": ticker, "action": "SELL", "error": str(e)})

            # Refresh cash AFTER sells — this is the freed-up capital
            portfolio.refresh_from_db()
            available_cash = float(portfolio.cash)

            # PHASE 2 — Solve LP for BUYS only, using updated cash, only positive-confidence tickers
            buy_indices = [i for i, s in enumerate(util_scores) if s > 0]
            if buy_indices:
                buy_tickers = [tickers[i] for i in buy_indices]
                buy_prices = [prices[i] for i in buy_indices]
                buy_scores = [util_scores[i] for i in buy_indices]

                c = [-s for s in buy_scores]
                A_ub = [buy_prices]
                b_ub = [available_cash]
                bounds = [(0, None) for _ in buy_indices]  # can only buy, qty >= 0

                res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

                if res.success:
                    for idx, delta_qty in enumerate(res.x):
                        ticker = buy_tickers[idx]
                        price = buy_prices[idx]
                        trade_qty = round(delta_qty, 2)
                        if trade_qty <= 0:
                            continue
                        try:
                            execute_buy(user, ticker, price, trade_qty)
                            trades_executed.append({"ticker": ticker, "action": "BUY", "qty": trade_qty})
                        except Exception as e:
                            failed_trades.append({"ticker": ticker, "action": "BUY", "error": str(e)})

            portfolio.refresh_from_db()
            return Response({
                "status": "Optimization processing complete",
                "trades_successful": trades_executed,
                "trades_failed": failed_trades,
                "remaining_cash": portfolio.cash
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LatestPriceView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            ticker = request.data.get("ticker")
            load_model(ticker)  # ensures price csv exists, auto-trains if needed
            df = pd.read_csv(BASE_DIR / f"data/price/{ticker}_price.csv")
            latest_price = float(df.iloc[-1]["Close"])
            latest_date = str(df.iloc[-1]["Date"])
            return Response({
                "ticker": ticker,
                "price": latest_price,
                "date": latest_date
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)