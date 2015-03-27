import sys
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.db import connection

from shopapp.weixin.models import SampleOrder


def awards(table_name,awdcode):
    cursor = connection.cursor()
    cursor.execute('select id from %s;'%table_name)
    
    sids = cursor.fetchall()
    print 'fetch total:',len(sids)
    
    cursor.close()
    update_rows = 0
    for sid in sids:
        row = SampleOrder.objects.filter(id=sid[0],status=0).update(status=awdcode)
        update_rows += row
    
    print "update total:",update_rows
    
if __name__ == "__main__":
    
    args = sys.argv
    if len(args) != 3:
        print "usage:python *.py <table_name> <awardcode>"
        
    print 'params:', args[1],args[2]
    
    awards(args[1],args[2]) 
