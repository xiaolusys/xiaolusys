#!/usr/bin/python
import MySQLdb
import time

def conn(cnt):
    print 'mysql connected %s times:%s'%(cnt,time.time())
    db = MySQLdb.connect(host="jconnfymhz868.mysql.rds.aliyuncs.com",    # your host, usually localhost
                     user="qiyue",         # your username
                     passwd="youni_2014qy",  # your password
                     db="shopmgr")        # name of the data base
    db.close()
    print 'mysql close %s times:%s'%(cnt,time.time())

from django.db import connection,transaction

def get_unionid_sql():
    return """
    SELECT 
        unionid
    FROM
        shop_weixin_unionid
    WHERE
        app_key = 'wx3f91056a2928ad2d'
    GROUP BY unionid having count(openid) > 1;
    """

def get_unique_sql():
    return """
    SELECT 
        id,modified
    FROM
        shop_weixin_unionid
    WHERE
        app_key = 'wx3f91056a2928ad2d'
        and unionid = %s;
    """
    
def rm_dirty_unionid():
    
    sql = get_unionid_sql()
    
    cursor = connection.cursor()
    cursor.execute(sql)
    unionids = cursor.fetchall()
    print 'fetch total:',len(unionids)
    
    usql = get_unique_sql()
    for uid in unionids:
        cursor.execute(usql,[uid[0]])
        rows = cursor.fetchall()
        if len(rows) > 1:
            luid = max(rows[0][0],rows[1][0])
            print 'debug luid:',luid 
            cursor.execute('delete from shop_weixin_unionid where id={}'.format(luid))
    
    cursor.close()
    transaction.commit_unless_managed() 


def rm_dirty_register():
    
    sql ="""
    SELECT 
        vmobile
    FROM
        flashsale_register
    GROUP BY vmobile
    HAVING COUNT(vmobile) > 1;
    """
    usql = """
    SELECT 
        id,vmobile
    FROM
        flashsale_register
    WHERE
        vmobile = %s
    ORDER BY mobile_pass DESC , modified DESC , id DESC;
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    vmobiles = cursor.fetchall()
    print 'fetch total:',len(vmobiles)
    for vm in vmobiles:
        cursor.execute(usql,[vm[0]])
        rows = cursor.fetchall()
        for row in rows[1:]:
            luid = row[0]
            print 'debug luid:',luid, row[1]
            cursor.execute('delete from flashsale_register where id={}'.format(luid))
    
    cursor.close()
    transaction.commit_unless_managed() 
    
    
if __name__ == '__main__':
    for i in range(1,10000):
        conn(i)
    
    
    