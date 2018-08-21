# -*- coding: utf-8 -*-


# PREFIX_X = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
PREFIX_X = '123456789'


def genLocationXList(xNum):
    xarray = [s for s in PREFIX_X]
    exarray = xarray
    if xNum <= len(xarray):
        return xarray[:xNum]

    for i, x in enumerate(xarray[:-1]):
        for y in xarray[i + 1:]:
            exarray.append(x + y)
            if len(exarray) >= xNum:
                return exarray
    return exarray


def genProductLocationList(locXNum, locYNum, locZNum):
    from shopback.archives.models import DepositeDistrict
    xArray = genLocationXList(locXNum)

    yArray = range(1, locYNum + 1)
    zArray = range(1, locZNum + 1)
    for x in xArray:
        for y in yArray:
            for z in zArray:
                DepositeDistrict.objects.get_or_create(
                    parent_no='%s%d' % (x, y), district_no=str(z))


def genPureNumLocationList(locXNum, locYNum, locZNum):
    from shopback.archives.models import DepositeDistrict
    xArray = genLocationXList(locXNum)

    yArray = range(1, locYNum + 1)
    zArray = range(1, locZNum + 1)
    for x in xArray:
        for y in yArray:
            for z in zArray:
                DepositeDistrict.objects.get_or_create(
                    parent_no='%s=%d' % (x, y), district_no=str(z))
