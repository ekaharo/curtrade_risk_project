from django.contrib.auth.models import User
from django.contrib.auth import login

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes


from knox.views import LoginView as KnoxLoginView

from trade_trans.models import TradeRqst

from .serializers import (TradeTranSerializer, LoginSerializer,
                    UserSerializer)

from trade_trans.trade_trans_usaidizi import which_take_profit 
from trade_trans.trade_trans_variables import signal_types


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class LoginAPI(KnoxLoginView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format = None):
        """make sure to put format = None"""
        print(self.request.data)
        serializer = LoginSerializer(data = self.request.data)         
        serializer.is_valid(raise_exception=True)
        """In the end if the serializer has no exceptions to make then we
        shall create the user below"""
        user = serializer.validated_data['user']
        print(f"{user}, User Presented for login")
        if user is not None:
            login(request, user)
            print(f"{user}, Has logged in")
            return super().post(request, format=None)
        return Response({'status': False,
                            'detail': 'Incorrect Phone Number and/or Password entered'})
       

class Trade_TransList(generics.ListCreateAPIView):
    queryset = TradeRqst.objects.all()
    serializer_class = TradeTranSerializer



class Trade_Trans_Detail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TradeRqst.objects.all()
    serializer_class = TradeTranSerializer

@api_view(['POST',])
@permission_classes([permissions.AllowAny])
def create_trade_rqst_view(request):
       
    # Since most of the validations are happening at
    # the model level we shall only check for the 
    # things we cannot accomodate with the model level validations

    # Check if data is valid first
    serializer = TradeTranSerializer(data = request.data)
    serializer.is_valid(raise_exception=True)

    # which take profit should we use ?

    take_profit = which_take_profit(
            take_profit1 = serializer.initial_data['take_profit1'],
            take_profit2 = serializer.initial_data['take_profit2'],
            entry_price = serializer.initial_data['entry_price']
        )
        
    if ((serializer.initial_data['signal_type'] in signal_types['buysignals'])\
            and (take_profit <= serializer.initial_data['entry_price'])\
            and (serializer.initial_data['entry_price'] <= serializer.initial_data['stop_loss'])):
        # discard this transaction no need for further calculations
        # if a buy signal with a take profit <= to entry price
        # or entry price is <= to stop loss
       
        content = {'status': f"Invalid Buy Signal request discarded without saving1 - {serializer.initial_data}"}
        print(content)
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    
    elif ((serializer.initial_data['signal_type'] in signal_types['sellsignals'])\
        and (take_profit >= serializer.initial_data['entry_price'])\
        and (serializer.initial_data['entry_price'] >= serializer.initial_data['stop_loss'])):
        # discard this transaction no need for further calculations
        # if sell signal rcvd with take profit >= entry price or
        # if entry price is >= stop loss
        content = {'status': f"Invalid SELL Signal request discarded without saving2 - {serializer.initial_data}"}
        print(content)
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    else:
        # We can save this request
        serializer.save()
        content = {'status': f"Valid Trade Request saved - {serializer.initial_data}"}
        print(content)
        return Response(content, status=status.HTTP_201_CREATED)
