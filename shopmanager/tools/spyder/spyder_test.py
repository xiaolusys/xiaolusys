#-*- coding:utf8 -*-
#我下载的网站是http://www.scriptlearn.com
#开始网页是http://www.scriptlearn.com
#FileName:test
from toolbox_insight import *
from Queue import Queue
import threading
import sys
num = int(raw_input('Enter the number of thread:'))
pnum = int(raw_input('Enter the number of download pages:'))
mainpage = str(raw_input('The mainpage:'))
startpage = str(raw_input('Start page:'))
queue = Queue()
key = Queue()
inqueue = Queue()
list = Newlist()
thlist = []
Flock = threading.RLock()
for i in range(num):
    th = reptile('th' + str(i), queue, key, Flock)
    thlist.append(th)
pro = proinsight(key, list, mainpage, inqueue)
pro.start()
for i in thlist:
    i.start()
queue.put(startpage)
for i in range(pnum):
    queue.put(inqueue.get())
for i in range(num):
    queue.put(None)