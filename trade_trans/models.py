from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q

from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


from rest_framework.response import Response

from trade_trans.trade_trans_usaidizi import (
        calculate_associated_risk, which_take_profit)


def validate_wlr(value):
    # check number not less than 0 (0%) or greater than 1 (100%)
    if (value < 0) or (value > 1):
        raise ValidationError(
            _(f"{value} decimal number btwn 0 and 1 Inclusive required e.g 0.2 for 20 per cent"),
            params={'value': value}
        )

def non_neg_or_zero(value):
    # Check number provided is non-negative or zero
    if value <= 0:
        raise ValidationError(
        _(f"{value} cannot be negative or zero"),
                params={'value': value}
    ) 

# Status of a request that was received for processing
RQ_ANALYSIS_STATUS = [
    ('WA', 'Waiting'),
    ('DC', 'Discarded'),
    ('PR', 'Processed'),
]

RQ2_ANALYSIS_STATUS = [
    ('WA', 'Waiting'),
    ('DC', 'Discarded'),
    ('PFR', 'Passed For Ranking'),
]

# Signal Options
SIGNAL_OPTIONS = [
    ('BL', 'Buy Limit'),
    ('BS', 'Buy Stop'),
    ('SS', 'Sell Stop'),
    ('SL', 'Sell Limit')
]

# TimeFrame Options available
TIMEFRAME_OPTIONS = [
    ('1H', '1 Hour'),
    ('4H', '4 Hours'),
    ('1D', '1 Day'),
    ('1W', '1 Week'),
    ('1M', '1 Month')
]

class TradeConstants(models.Model):
    """System Constants"""
    be_ratio = models.FloatField(verbose_name="BreakEven Ratio (BE RATIO)", default=0.05)
    risk_threshold = models.FloatField(verbose_name="Risk Threshold", default=0.075)
    trans_auto_correlate = models.PositiveIntegerField(
        verbose_name="Transactions to Wait before Correlating",
                        default=10)

    def __str__(self):
        return f"BE - {self.be_ratio}, Risk Threshold - {self.risk_threshold}"


class TradeRqst(models.Model):
    """All requests to the risk management module are stored here
    if VALID"""

    requestor = models.ForeignKey(User, on_delete=models.CASCADE)
    trade_id = models.IntegerField(verbose_name="RQSTID", unique=True, 
        error_messages= {'unique': "Another Request with a similar ID exists"})
    wlr = models.FloatField(verbose_name="Win/Loss Ratio", max_length=7,
                    validators=[validate_wlr])
    entry_price = models.FloatField(verbose_name="Entry Point",
        max_length=7, validators=[non_neg_or_zero])
    take_profit1 = models.FloatField(verbose_name="Supplied Take Profit1",
        max_length=7, validators=[non_neg_or_zero])
    take_profit2 = models.FloatField(verbose_name="Supplied Take Profit2", max_length=7,
        blank=True, null=True, validators=[non_neg_or_zero])
    signal_type = models.CharField(max_length=15,
                    verbose_name="Signal Type", choices=SIGNAL_OPTIONS)
    time_frame = models.CharField(verbose_name="Time Frame",
        choices = TIMEFRAME_OPTIONS, max_length=15)
    stop_loss = models.FloatField(verbose_name="Stop Loss", max_length=7,
        validators=[non_neg_or_zero])
    asset = models.CharField(max_length=15, verbose_name="Asset")
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RqstID-{self.trade_id}asset : Signal Type - {self.signal_type} : \
                    Asset Type - {self.asset} : Created - {self.created_at}"

class RqAnal(models.Model):
    """Analysis of request rcvd is stored here after calculation using a helper function"""
    rqst_id = models.ForeignKey(TradeRqst, on_delete=models.CASCADE,
        verbose_name="Trade Request ID")
    calc_pd = models.TextField(verbose_name="Risk Calculation Results (DataFrame)")
    risk = models.FloatField(verbose_name="Calculated RISK for Request, x 100 to get %")
    expected_return = models.FloatField(verbose_name="Expected Return , x 100 to get %")
    status = models.CharField(verbose_name="Request Status",
        choices=RQ_ANALYSIS_STATUS, max_length=9)
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rqst_id} Status-{self.status} Risk%-{self.risk}"

# Signal triggered by a succesful traderqst object created
@receiver(post_save, sender=TradeRqst)
def calc_risk_save_results(sender, instance=None, created=False, **kwargs):
    if created:
        print(f"{instance} Risk Calculation triggered")

        tc = TradeConstants.objects.all().first()
        be_ratio = tc.be_ratio
        risk_threshold = tc.risk_threshold
        
        # evaluate the take profit to use - Use one closest to entry point

        result = calculate_associated_risk(be_ratio = be_ratio, win_loss_ratio = instance.wlr, asset = instance.asset,
                        signal_type = instance.signal_type, entry = instance.entry_price,
                        take_profit1 = instance.take_profit1, take_profit2 = instance.take_profit2,
                        stop_loss = instance.stop_loss, risk_threshold = risk_threshold)
        print(f"Result of calculation {result}")
        if result['risk'] > risk_threshold:
            status = "DC"
            comments = f"RISKY {result['risk']:.4%} , \
                above defined risk threshold of {risk_threshold:.4%}, \
                return expected {result['e_return']:.4%} \
                used takeprofit {result['tp_used']}"
        else:
            status = "WA"
            comments = f"Accepted for further processing, \
                Calculated Risk {result['risk']:.4%},\
                defined Risk Threshold {risk_threshold:.4%}, \
                return expected {result['e_return']:.4%} \
                used takeprofit {result['tp_used']}"

        RqAnal.objects.create(
            rqst_id = instance,
            calc_pd = result['df'],
            risk = result['risk'],
            expected_return = result['e_return'],
            status = status,
            comments = comments ,
        )

# Signal Triggered by creation of a succesful RqAnal which is not RISKY
# None Risky Transactions off course are ready to be correlated
@receiver(post_save, sender=RqAnal)
def create_corr_trans(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.status == 'DC':
            # No need saving a discarded original signal or further processing
            print(f"{instance} Not saved in Correlation Trans Table")
            pass
        else:
            print(f"{instance} signal passed to Stage 2 Store for Correlation")
            CorrelationTrans.objects.create(
                corr_id = instance,
                asset = instance.rqst_id.asset,
                issue_time = instance.rqst_id.created_at,
                time_frame = instance.rqst_id.time_frame,
                entry_price = instance.rqst_id.entry_price,
                trade_id = instance.rqst_id.trade_id,
                comments = "created"
            )
            result = CorrelationTrans.objects.filter(corr_id=instance).first()
            print(f"{result} saved in Correlation Transaction DB succesfully")
            print(f"Checking for Nos of similar Trans waiting....")
            # how many transactions falling in the same time frame are waiting ?
            r_10 = CorrelationTrans.objects.filter(Q(status='WA') & Q(time_frame=result.time_frame))
            print(f"Query of r_10 is {r_10}")

            # get the default set transactions to correlate
            t_c = TradeConstants.objects.all().first().trans_auto_correlate
            
            if len(r_10) > (t_c-1):
                output1 = f"Transaction Count:{len(r_10)},threshold {t_c}..proceeding to correlate"
                result.comments += f" >> {output1}"
                result.save()
                print(output1)
            else:
                output2 = f"Transaction Count:{len(r_10)},threshold {t_c}..storing for later processing"
                result.comments += f" >> {output2}"
                result.save()
                print(output2)

class CorrelationTrans(models.Model):
    """Correlation Transaction Table Storing results for signals that 
    passsed stage1 Plus various correlation stages processing status"""
    corr_id = models.ForeignKey(RqAnal, on_delete=models.CASCADE,
        verbose_name="Forwarded Request Analysis ID")
    asset = models.CharField(max_length=15, verbose_name="Asset")
    issue_time = models.DateTimeField()
    time_frame = models.CharField(verbose_name="Time Frame",
        choices = TIMEFRAME_OPTIONS, max_length=15)
    entry_price = models.FloatField(verbose_name="Entry Price")
    trade_id = models.PositiveIntegerField(verbose_name="Original Trade ID")
    corr_nos = models.PositiveIntegerField(
        verbose_name="How many times has this rqst been correlated ?", 
        default=0)
    comments = models.TextField()
    status = models.CharField(verbose_name="Request Status",
        choices=RQ2_ANALYSIS_STATUS, max_length=20, default='WA')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.corr_id}:Asset {self.asset} : \
            IssueTime {self.issue_time}:\
            TimeFrame {self.time_frame}:\
            Status {self.status} :Comments {self.comments[:20]}"