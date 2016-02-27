import sys
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import connection

from flashsale.promotion.models import XLSampleOrder
from flashsale.push import mipush
from flashsale.protocol import get_target_url
from flashsale.protocol import constants

def get_award_sql():
    return """ 
        SELECT 
            fps.id,fps.customer_id
        FROM
            flashsale_promotion_sampleorder fps
                LEFT JOIN
            flashsale_promotion_invitecount fpi ON fps.customer_id = fpi.customer_id
        WHERE
            fps.status = 0
                AND fpi.invite_count >= {0}
                    AND fps.created > '2016-02-22'
        ORDER BY fpi.invite_count desc;
    """

award_msg = "实况战报：卡通睡袋中奖名单已经出炉，您可以享用了，600万红包还剩余345万，快快抢吧！！！"

def push_phone_account(account_id):
    mipush.mipush_of_ios.push_to_account(
        account_id,
        {'target_url': get_target_url(constants.TARGET_TYPE_HOME_TAB_1)},
        description=award_msg
    )
    mipush.mipush_of_android.push_to_account(
        account_id,
        {'target_url': get_target_url(constants.TARGET_TYPE_HOME_TAB_1)},
        description=award_msg
    )

def awards(invite_cnt,awdcode):
    
    cursor = connection.cursor()
    cursor.execute(get_award_sql().format(invite_cnt))
    sids = cursor.fetchall()
    print 'fetch total:',len(sids)
    cursor.close()
    
    update_rows = 0
    for sid in sids:
        row = XLSampleOrder.objects.filter(id=sid[0],status=0).update(status=awdcode)
        if row > 0:
            push_phone_account(int(sid[1]))
        update_rows += row
    
    print "update total:",update_rows
    
if __name__ == "__main__":
    
    args = sys.argv
    if len(args) != 3:
        print "usage:python *.py <invite_cnt> <awardcode>"
        
    print 'params:', args[1],args[2]
    
    awards(int(args[1]),int(args[2])) 
