import datetime
import json
from datetime import timedelta


def week_range(date):
    if isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date.date(), datetime.time.min)

    year, week, dow = date.isocalendar()

    # Find the first day of the week.
    if dow == 1:
        # Since we want to start with Sunday, let's test for that condition.
        start_date = date
    else:
        delta = dow - 1
        # Otherwise, subtract `dow` number days to get the first day
        start_date = date - timedelta(delta)

    # Now, add 6 for the last day of the week (i.e., count up to Saturday)
    end_date = start_date + timedelta(6)
    if isinstance(start_date, datetime.datetime):
        end_date = datetime.datetime.combine(end_date, datetime.time.max)

    return (start_date, end_date)


def day_range(date):
    return (
        datetime.datetime.combine(date, datetime.time.min),
        datetime.datetime.combine(date, datetime.time.max)
    )


def parse_str2date(date_str, format='%Y-%m-%d'):
    return datetime.datetime.strptime(date_str, format)


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


weekdays = ['Monday','Tuesday','Wednesday','Thursday',
            'Friday','Saturday','Sunday']

def get_previous_byday(dayname, start_date=None):
    if start_date is None:
        start_date = datetime.date.today()

    day_num = start_date.weekday()
    day_num_target = weekdays.index(dayname)

    days_ago = (7 + day_num - day_num_target) % 7
    if days_ago == 0:
        days_ago = 7

    target_date = start_date - timedelta(days = days_ago)
    return target_date


