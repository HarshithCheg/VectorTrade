from rest_framework import serializers
from .models import Portfolio, Position, Trade, User

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

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uid', 'first_name', 'last_name', 'email', 'username', 'password', 'date_joined',)
        read_only_fields = ('uid', 'date_joined')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password is not None:
            user.set_password(password)
            user.save()
        else:
            raise serializers.ValidationError("Enter a Valid Password.")
        return user        

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data['username']
        password = data['password']
        try:
            user = User.objects.get(username= username)
            if not user.check_password(password):
                raise serializers.ValidationError("Incorrect Password")
        except User.DoesNotExist:
            raise serializers.ValidationError("Username Does Not Exist")
        
        return user
    
class PredictSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    # date_start = serializers.DateField()
    # date_end = serializers.DateField()

    # def validate(self, data):
    #     ticker = data["ticker"]
    #     start = data["date_start"]
    #     end = data["date_end"]
    #     if start > end:
    #         raise serializers.ValidationError("Start Date Must be before End Date")
    #     return data