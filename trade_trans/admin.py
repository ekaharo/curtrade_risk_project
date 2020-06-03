from django.contrib import admin
from .models import TradeRqst, RqAnal, TradeConstants, CorrelationTrans

admin.site.register(TradeRqst)
admin.site.register(RqAnal)
admin.site.register(TradeConstants)
admin.site.register(CorrelationTrans)