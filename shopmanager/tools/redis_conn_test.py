#!/usr/bin/env python
import random
import datetime
import redis

CHAR_LIST = list('abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMN')

def gen_cache_data_list(max_lines):
    lines = []
    for i in xrange(max_lines):
        lines.append(random.sample(CHAR_LIST, random.randint(10, 30)))
    return lines

def test_cache_performance():
    data_list = gen_cache_data_list(100000)
    r = redis.Redis(host='192.168.1.200', port=6379, db=0)
    next_line=0
    count_lines=len(data_list)
    print 'test cache performance start: %s'% datetime.datetime.now()
    while next_line+1<count_lines:
        r.set(str(next_line),data_list[next_line])
        next_line=next_line+1

    print 'test cache performance end: %s' % datetime.datetime.now()

def test_connection_state():
    conn_list = []
    r = redis.Redis(host='192.168.1.200', port=6379, db=0)
    next_line=0
    count_lines=len(data_list)
    print 'test cache performance start: %s'% datetime.datetime.now()
    while next_line+1<count_lines:
        r.set(str(next_line),data_list[next_line])
        next_line=next_line+1

    print 'test cache performance end: %s' % datetime.datetime.now()

def main():
    pass



if __name__=='__main__':

       main()