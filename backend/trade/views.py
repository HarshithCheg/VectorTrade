from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Portfolio, Position, Trade
from .serializers import PortfolioSerializer, TradeSerializer, PositionSerializer, LoginSerializer, RegisterSerializer, PredictSerializer
from decimal import Decimal
from utils import load_model, BASE_DIR
import pandas as pd
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
                "signal": signal
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        