from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.response import Response

from .models import TradeRqst


class UserSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        style = {'input_type': 'password' }, trim_whitespace = False)
    
    def validate(self, data):
        print(f"{data}")
        username = data.get('username')
        password = data.get('password')

        if username and password:
            if User.objects.filter(username=username).exists():
                user = authenticate(request = self.context.get('request'), username=username, password=password)
                print(f"{user}")
                data['user'] = user
                return data

            else:
                msg = {
                    'status' : False,
                    'detail' : 'UserName not found, Have you registered ?'
                }
                # return Response({'status': False,
                #     'detail': 'Phone number not found, Have you registered ?'})
                raise serializers.ValidationError(msg, code = 'authorization')

            if not user:
                msg = {
                    'status' : False,
                    'detail' : 'Username and/or Password entered'
                }
                raise serializers.ValidationError(msg)
                # return Response({'status': False,
                #     'detail': 'Incorrect Phone Number and/or password'})
        else:
            msg = {
                'status' : False,
                'detail' : 'Username and/or password not entered'
            }
            raise serializers.ValidationError(msg, code = 'authorization')

class TradeTranSerializer(serializers.ModelSerializer):
        
    class Meta:
        fields = ('id','requestor', 'trade_id', 'signal_type',
                    'wlr', 'entry_price', 'take_profit1', 'take_profit2',
                    'time_frame', 'stop_loss', 'asset'
                 )

        model = TradeRqst