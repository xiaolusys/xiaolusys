#-*- coding:utf8 -*-
from sgmllib import SGMLParser
import threading
import time
import urllib2
import StringIO
import gzip
import string
import os
#rewrite SGMLParser for start_a
class Basegeturls(SGMLParser):   #这个Basegeturls类作用是分析下载的网页，把网页中的所有链接放在self.url中。
    def reset(self):
        self.url = []
        SGMLParser.reset(self)
    def start_a(self, attrs):
        href = [v for k, v in attrs if k == 'href']
        if href:
            self.url.extend(href)
#for quickly finding
class Newlist(list):#这个类其实是一个添加了find方法的LIST。当num变量在LIST中，返回True,当不在LIST中，返回False并把num按二分法插入LIST中
    def find(self, num):
        l = len(self)
        first = 0
        end = l - 1
        mid = 0
        if l == 0:
            self.insert(0,num)
            return False
        while first < end:
            mid = (first + end)/2
            if num > self[mid]:
                first = mid + 1
            elif num < self[mid]:
                end = mid - 1
            else:
                break
        if first == end:
            if self[first] > num:
                self.insert(first, num)
                return False
            elif self[first] < num:
                self.insert(first + 1, num)
                return False
            else:
                return True
        elif first > end:
            self.insert(first, num)
            return False
        else:
            return True
#下面的reptile顾名思义是一个爬虫
class reptile(threading.Thread):
    #Name:       是爬虫是名字，queue是任务队列，所有的爬虫共用同一个任务队列
    #从中取出一个任务项进行运行，每个任务项是一个要下载网页的URL
    #result:     也是一个队列，将下载的网页中包含的URL放入该队列中
    #inittime:   在本程序中没有用，只是一个为了以后扩展用的
    #downloadway:是下载的网页存放的路径
    #configfile: 是配置文件，存放网页的URL和下载下后的路径
    #maxnum:     每个爬虫有个最大下载量，当下载了这么多网页后，爬虫dead
    def __init__(self, Name, queue, result, Flcok, inittime = 0.00001, downloadway = 'D:\\bbs\\',configfile = 'D:\\bbs\\conf.txt', maxnum = 10000):
        threading.Thread.__init__(self, name = Name)
        self.queue = queue
        self.result = result
        self.Flcok = Flcok
        self.inittime = inittime
        self.mainway = downloadway
        self.configfile = configfile
        self.num = 0          #已下载的网页个数
        self.maxnum = maxnum
        os.makedirs(downloadway + self.getName())      #系统调用：在存放网页的文件夹中创建一个以该爬虫name为名字的文件夹
        self.way = downloadway + self.getName() + '\\'
    def run(self):
        opener = urllib2.build_opener()     #创建一个开启器
        while True:
            url = self.queue.get()          #从队列中取一个URL
            if url == None:                 #当取得一个None后表示爬虫结束工作，用于外部方便控制爬虫的生命期
                break
            parser = Basegeturls()          #创建一个网页分析器
            request = urllib2.Request(url) #网页请求
            request.add_header('Accept-encoding', 'gzip')#下载的方式是gzip压缩后的网页，gzip是大多数服务器支持的一种格式
            try:                                         #这样可以减轻网络压力
                page = opener.open(request)#发送请求报文
                if page.code == 200:       #当请求成功
                    predata = page.read() #下载gzip格式的网页
                    pdata = StringIO.StringIO(predata)#下面6行是实现解压缩
                    gzipper = gzip.GzipFile(fileobj = pdata)
                    try:
                        data = gzipper.read()
                    except(IOError):
                        print 'unused gzip'
                        data = predata#当有的服务器不支持gzip格式，那么下载的就是网页本身
                    try:
                        parser.feed(data)#分析网页
                    except:
                        print 'I am here'#有的网页分析不了，如整个网页就是一个图片
                    for item in parser.url:
                        self.result.put(item)#分析后的URL放入队列中
                    way = self.way + str(self.num) + '.html'#下面的是网页的保存，不多说了
                    self.num += 1
                    file = open(way, 'w')
                    file.write(data)
                    file.close()
                    self.Flcok.acquire()
                    confile = open(self.configfile, 'a')
                    confile.write( way + ' ' + url + '\n')
                    confile.close()
                    self.Flcok.release()
                page.close()
                if self.num >= self.maxnum:#达到最大量后退出
                    break
            except:
                print 'end error'
#和爬虫一样是个线程类,作用是将爬虫中的result中存入的URL加以处理。只要同一个服务器的网页
class proinsight(threading.Thread):
    def __init__(self, queue, list, homepage, inqueue):
        threading.Thread.__init__(self)
        self.queue = queue#和爬虫中的result队列是同一个
        self.list = list#是上面Newlist的对象
        self.homepage = homepage#主页
        self.inqueue = inqueue#处理完后的URL的去处
    def run(self):
        length = len(self.homepage)
        while True:
            item = self.queue.get()
            if item == None:
                break
            if item[0:4] == '\r\n':
                item = item[4:]
            if item[-1] == '/':
                item = item[:-1]
            if len(item) >= len('http://') and item[0:7] == 'http://':
                if len(item) >= length and item[0:length] == self.homepage:
                    if self.list.find(item) == False:
                        self.inqueue.put(item)
            elif item[0:5] == '/java' or item[0:4] == 'java':
                pass
            else:
                if item[0] != '/':
                    item = '/' + item
                item = self.homepage + item
                if self.list.find(item) == False:
                    self.inqueue.put(item)
                    