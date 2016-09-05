# coding=utf-8
__author__ = 'meron'
from django.core.management.base import BaseCommand

import datetime
from flashsale.pay.models import Customer, SaleTrade

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('poll_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help='Delete poll instead of closing it')

    def handle(self, *args, **options):


        stats = {}
        for line in reader:
          if line[0] == 'id':
            continue
          if line[2] == 'NULL':
            continue
          cid = int(line[0])
          first = datetime.datetime.strptime(line[2], '%Y-%m-%d %H:%M:%S')
          current = datetime.datetime.strptime(line[4], '%Y-%m-%d %H:%M:%S')
          section = stats.get(first.strftime('%Y-%W'), {})
          total = section.get(0, set())
          delta = current - first
          month = section.get((delta.days / 7) + 1, set())
          total.add(cid)
          month.add(cid)
          section[0] = total
          section[(delta.days/7)+1] = month
          stats[first.strftime('%Y-%W')] = section

        stats2 = {}
        for k, v in stats.items():
          newv = {}
          if k in ('2015-27','2015-28','2015-29'):
            print 'k=',k , v
          for k2, v2 in v.items():
            newv[k2] = len(v2)
          stats2[k] = newv

        #print stats2
        datas = []
        for k, v in stats2.items():
          i = [k] + ['0']*100
          for k2, v2 in v.items():
            i[k2+1] = str(v2)
          if k in ('2015-27','2015-28','2015-29'):
            print 'k=', i
          datas.append(i)

        sfile = open('data2.csv', 'w')
        for data in datas:
        #    print 'data:', ','.join(data)
        #    print >> sfile, ','.join(data)
            sfile.write(','.join(data))
            sfile.write('\n')
        sfile.close()

