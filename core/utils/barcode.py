# coding: utf8
from __future__ import absolute_import, unicode_literals

def number2char(number):
    return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[int(number) % 26]

def gen(digit_num=5, prefix='', begin='00001'):
    if int(begin) >= int('9'*6):
        raise ValueError("begin value gretter then the max value of digit_num")

    code = '%0{digit_num}d'.format(digit_num=digit_num)%(int(begin)+1)
    return '%s%s'%(prefix, code)

def encode(barcode, extras=[]):
    return '-'.join([barcode] + extras)

def decode(barcode):
    return barcode.split('-')[0]

def extras(barcode):
    return barcode.split('-')[1:-1]