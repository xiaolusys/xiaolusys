# -*- coding:utf8 -*-
import re
from django.db.models import Q
from shopapp.yunda.models import ClassifyZone, BranchZone


def get_addr_zones(s, c, d, address=''):
    lstate = len(s) > 1 and s[0:2] or ''
    lcity = len(c) > 1 and c[0:2] or ''
    ldistrict = len(d) > 1 and d[0:2] or ''

    if d:
        if address and ldistrict == u'吴江' and lstate == u'江苏':

            szds = None
            try:
                sz = BranchZone.objects.get(barcode='215201')
            except BranchZone.DoesNotExist:
                pass
            else:
                szds = [z.city for z in sz.classify_zones]
                if szds:
                    rp = re.compile('|'.join(szds))
                    if rp.search(address):
                        return sz

        czones = ClassifyZone.objects.filter(Q(city__startswith=ldistrict) | Q(district__startswith=ldistrict),
                                             state__startswith=lstate)
        if czones.count() == 1:
            return czones[0].branch

        for czone in czones:
            if czone.city == d or czone.district == d:
                return czone.branch

    if c:
        czones = ClassifyZone.objects.extra(select={'city_length': "length(city)"}) \
            .filter(state__startswith=lstate,
                    city__startswith=lcity, district='').order_by('-city_length')
        if czones.count() == 1:
            return czones[0].branch

        for czone in czones:
            if czone.city.startswith(c):
                return czone.branch

        if czones.count() > 0:
            return czones[0].branch

    if s:
        czones = ClassifyZone.objects.filter(state__startswith=lstate,
                                             city='', district='')
        if czones.count() == 1:
            return czones[0].branch

        for czone in czones:
            if czone.state == s:
                return czone.branch

    return None
