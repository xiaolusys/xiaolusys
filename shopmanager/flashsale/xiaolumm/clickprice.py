import datetime


CLICK_TIME_PRICE = (
    (datetime.datetime(2015,6,1,0,0,0),datetime.datetime(2015,6,1,10,0,0),0),
    (datetime.datetime(2015,6,1,10,0,0),datetime.datetime(2015,6,1,23,59,59),50),
)

def calc_Time_Slice_Click_Price(click_qs,ori_price=0):
    
    click_price_list = []
    for df,dt,price in CLICK_TIME_PRICE:
        
        click_price = max(price,ori_price)
        click_count = click_qs.filter(created__range=(df, dt)).count()
        click_price_list.append((df,dt,click_count,click_price))
        
    return click_price_list