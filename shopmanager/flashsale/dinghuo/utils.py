__author__ = 'yann'
import datetime


def parse_datetime(target_time_str):
    return datetime.datetime.strptime(target_time_str, '%Y-%m-%d %H:%M:%S')


def parse_date(target_date_str):
    try:
        year, month, day = target_date_str.split('-')
        target_date = datetime.date(int(year), int(month), int(day))
        return target_date
    except:
        return datetime.date.today()
