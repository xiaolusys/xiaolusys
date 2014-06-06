#-*- coding:utf8 -*-
import os
import re
import csv, codecs, cStringIO
from django.conf import settings


def handle_uploaded_file(f,fname):
    
    filename = os.path.join(settings.DOWNLOAD_ROOT,fname)
    with open(filename, 'wb+') as dst:
        for chunk in f.chunks():
            dst.write(chunk)
    return filename


def gen_cvs_tuple(qs,fields=[],title=[]):
    """ 获取queryset tuple """
    qs_tuple = [title]
    
    for q in qs:        
        ks = []
        for k in fields:
            if k.find('.')&k.find('__') != -1:
                pk,sk = re.split('\.|__',k)
                ks.append('%s'%(unicode(getattr(getattr(q,pk,None),sk,None)) or '-'))
                continue
            ks.append('%s'%(unicode(getattr(q,k,None)) or '-'))
        
        qs_tuple.append(ks)
        
    return qs_tuple


class CSVUnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue,delimiter=',',
                            quotechar='"', dialect=dialect, **kwds)
        self.stream = f
        self.encoding = encoding
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode(self.encoding) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode(self.encoding)
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
            
