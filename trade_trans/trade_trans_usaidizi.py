"""Helper Functions"""
def calculate_associated_risk(**kwargs):
    """
    Calculates the risk for each signal/request received
    Invoked after succesful save of a request
    Takes Unlimited number of Kwargs
    Returns a dictionary populated with
    1) e_return - calculated return of the request as a decimal 
        (multiply by 100 to get %)
    2) risk - calculated risk of the request
        (multiply by 100 to get %)
    3) df - string of a Dataframe holding all the calculation parameters
        Just for information only.
    4) take_profit figure used when we receive two take profits
    """
    
    import pandas as pd
    import numpy as np
    from trade_trans.trade_trans_usaidizi import which_take_profit
    from trade_trans.trade_trans_variables import signal_types    
    
    be_ratio = kwargs['be_ratio']
    win_loss_ratio = kwargs['win_loss_ratio']
    asset = kwargs['asset']
    signal_type = kwargs['signal_type']
    entry = kwargs['entry']
    take_profit1 = kwargs['take_profit1']
    take_profit2 = kwargs['take_profit2']
    stop_loss = kwargs['stop_loss']
    risk_threshold = kwargs['risk_threshold']
    
    risk_assessment_report = {} # dict to hold results
    
    
    # determine which take profit figure to use between take profit 1 and 2
    # using the helper function which_take_profit

    take_profit = which_take_profit(take_profit1=take_profit1,\
        take_profit2=take_profit2 , entry_price=entry)

    risk_assessment_report['tp_used'] = take_profit 
    
    # This validation is not required as it exists on the model level before
    # saving the request BUT lets just leave it for now
 
    # create a 3 x 4 starting numpy array

    calc_template = np.zeros((3,4))

    # Create dataframe to hold our values

    df= pd.DataFrame(data=calc_template, 
                     index=['take_profit', 'entry', 'stop_loss'],
                    columns=['points', 'pips', 'probs', 'return'])

    # populate points

    df['points'] = np.array([take_profit, entry, stop_loss])

    # calculate pips
    
    tp_pip = df.loc['take_profit', 'points'] - df.loc['entry', 'points']
    tp_e = tp_pip * (1-win_loss_ratio)
    
    if tp_e < 0:
        tp_e = tp_e * - 1
    
    tp_sl = df.loc['stop_loss', 'points'] - df.loc['entry', 'points']
    
    if (signal_type in signal_types['sellsignals']):
        # For sell signals difference btwn tp and entry 
        # will be negative convert to positive
        # Similar for stop loss it will be positive convert to negative
        # The rest of the calculation remains the same
        tp_pip = (tp_pip * -1)
        tp_sl = (tp_sl * - 1)
    
    arr = np.array([tp_pip, tp_e, tp_sl])

    df['pips'] = arr

    # populate probabilities

    df['probs'] = np.array([
        win_loss_ratio-be_ratio,
        be_ratio,
        1-win_loss_ratio
    ])

    # calculate & populate returns

    df['return'] = np.array([
       df.loc['take_profit', 'pips'] /df.loc['entry', 'points'],
        df.loc['entry', 'pips']/df.loc['entry', 'points'],
        df.loc['stop_loss', 'pips'] / df.loc['entry', 'points']    
    ])


    # Create new calculated column for individual expected returns

    df['expect_return'] = df['probs'] * df['return']

    # calculate expected return - mean of returns

    e_return = df['return'].mean()
    risk_assessment_report['e_return'] = e_return

    # create new column for difference btwn return and mean of returns - e_return

    df['diff_return_mean_returns'] = df['return'] - e_return
    

    # Get the Standard Deviation establish the risk

    how_risky = np.std(df['diff_return_mean_returns'])

    how_risky
    # Evaluate how_risky vs threshold
    
    risk_assessment_report['risk'] = how_risky
    risk_assessment_report['df'] = df
    return risk_assessment_report


def which_take_profit(**kwargs):
    """Choose which take profit figure to utilise
    """
    take_profit1 = kwargs['take_profit1']
    take_profit2 = kwargs['take_profit2']
    entry_price = kwargs['entry_price']

    try:
        difftp2 = take_profit2 - entry_price
        
    except:
        # take profit 2 empty or not supplied , use take profit 1
        take_profit = take_profit1
        print(f"2 Used Take Profit 1 since Take Profit 2 not provided - {take_profit2}")
        return take_profit
    else:
        difftp1= take_profit1-entry_price
        if ((difftp2 < 0) and (difftp1)) < 0:
            print(f"3 Both Take Profits provided when sub from entry were negative difftp1 {difftp1}, difftp2 {difftp2}")
            if difftp2 > difftp1 :
                take_profit = take_profit2
                print(f"4 Both Take Profits provided when sub from entry were negative BUT {difftp2} > {difftp1}\
                    so using take_profit2 {take_profit}")                
                return take_profit
            else:
                take_profit = take_profit1
                print(f"5 Both Take Profits provided when sub from entry were negative BUT {difftp1} > {difftp2}\
                    so using take_profit1 {take_profit}") 
                return take_profit
        
        elif difftp2 < 0:
            take_profit = take_profit1
            print(f"6 difftp2 less than 0 - {difftp2}\
                    so using take_profit1 {take_profit}") 
            return take_profit
        
        elif difftp1 < 0:
            take_profit = take_profit2
            print(f"7 difftp1 less than 0 - {difftp1}\
                    so using take_profit2 {take_profit}") 
            return take_profit
            
        elif difftp1 <= difftp2:
            take_profit = take_profit1
            print(f"8 difftp1 {difftp1} less than or equal to difftp2 {difftp2}\
                    so using take_profit2 {take_profit}") 
            return take_profit
        else:
            take_profit = take_profit2
            print(f"8 difftp2 {difftp2} greater than  to difftp1 {difftp1}\
                    so using take_profit2 {take_profit}") 
            return take_profit           


