from django.urls import path

from .views import (LoginAPI, Trade_TransList,
        Trade_Trans_Detail, create_trade_rqst_view)

from knox.views import LogoutAllView

urlpatterns = [
    path('login/', LoginAPI.as_view()), # user login endpoint
    path('logout/', LogoutAllView.as_view()), 
    # user logout endpoint, deletes all user tokens
    path('<int:pk>/', Trade_Trans_Detail.as_view()),
    path('', Trade_TransList.as_view()),
    path('new_td_rqst/', create_trade_rqst_view, name='new_td_rqst'),
]
