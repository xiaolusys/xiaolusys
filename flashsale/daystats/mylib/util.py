# encoding=utf8
from datetime import datetime, date, timedelta


def groupby(iterable, func):
    data = {}
    for item in iterable:
        key = func(item)

        if isinstance(key, datetime):
            key = key.date()

        if data.get(key, None):
            data[key].append(item)
        else:
            data[key] = [item]
    return data


def process(data, func):
    res = []
    for k, v in data.items():
        if isinstance(k, date):
            k = k.strftime('%Y-%m-%d')
        k = str(k)
        res.append((k, func(v)))
    return res


def process_data(data, func):
    data = groupby(data, func)
    data = process(data, len)
    data = sorted(data, key=lambda x: x[0], reverse=False)
    return data


def format_datetime(datetime):
    return datetime.strftime('%Y-%m-%d %H:%M:%S')


def format_date(datetime):
    return datetime.strftime('%Y-%m-%d')


def get_date_from_req(req):
    now = datetime.now()
    last = now - timedelta(days=7)
    now = now + timedelta(days=1)
    p_start_date = req.GET.get('start_date', '%s-%s-%s' % (last.year, last.month, last.day))
    p_end_date = req.GET.get('end_date', '%s-%s-%s' % (now.year, now.month, now.day))
    start_date = datetime.strptime(p_start_date, '%Y-%m-%d')
    end_date = datetime.strptime(p_end_date, '%Y-%m-%d')
    return p_start_date, p_end_date, start_date, end_date


def generate_range(x, nums):
    result = []
    for i, num in enumerate(nums):
        left = nums[i-1] if i-1 >= 0 else None
        right = nums[i+1] if i + 1 < len(nums) else None

        if not left and x < num:
            return u'小于%s' % num

        if not right and x >= num:
            return u'大于%s' % num

        if in_range(x, num, right):
            res = '%s-%s' % (num, right)
            return res
    return result


def in_range(num, left, right):
    return left <= num < right


if __name__ == '__main__':
    for i in range(0, 25):
        print i, generate_range(i, [10, 20, 30, 50, 100])
