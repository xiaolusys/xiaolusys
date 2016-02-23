import sys
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import connection

from flashsale.promotion.models import XLSampleOrder

def get_award_sql():
    return """ 
        SELECT 
            fps.id
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
    
def awards(invite_cnt,awdcode):
    
    cursor = connection.cursor()
    cursor.execute(get_award_sql().format(invite_cnt))
    
    sids = cursor.fetchall()
    print 'fetch total:',len(sids)
    
    cursor.close()
    update_rows = 0
    for sid in sids:
        row = XLSampleOrder.objects.filter(id=sid[0],status=0).update(status=awdcode)
        update_rows += row
    
    print "update total:",update_rows
    
if __name__ == "__main__":
    
    args = sys.argv
    if len(args) != 3:
        print "usage:python *.py <invite_cnt> <awardcode>"
        
    print 'params:', args[1],args[2]
    
    awards(args[1],args[2]) 
