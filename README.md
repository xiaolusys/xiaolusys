
xiaolusys
_______________________
1, enviroment;
2, api rule;
3, oneapm statsd;
4, git command;
5, test case;
6, logger;

[![Build Status](http://git.xiaolumm.com:8000/api/badges/xiaolumm/xiaolusys/status.svg)](http://git.xiaolumm.com:8000/xiaolumm/xiaolusys)

## Table of Contents

- [About](#about)
- [Installation](#installation)
- [TestCase](#testcase)
- [Statsd](#statsd)
- [ApiRule](#apirule)
- [Celery](#celery)
- [Migrate](#migrate)
- [Logger](#logger)

## About
- [Python](https://www.python.org/)
- [Django](https://docs.djangoproject.com/en/1.8/)
- [Djangorestframework](http://www.django-rest-framework.org/)

## Installation
``` shell
$ sudo apt-get update;apt-get install -y gcc libxml2-dev libxslt1-dev python-dev libmysqld-dev libjpeg-dev python-pip
$ sudo pip install --upgrade virtualenv
$ cd xiaolusys & virtualenv ve & source ve/bin/activate
$ pip install -i http://pypi.oneapm.com/simple --upgrade blueware
$ pip install -i http://pypi.oneapm.com/simple --upgrade oneapm-ci-sdk
$ pip install -i http://mirrors.aliyun.com/pypi/simple -r requirements_production.txt
$ python manage runserver
## you are install success when console print below:
August 14, 2016 - 23:55:57
Django version 1.8.10, using settings 'shopmanager.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
``` 

## TestCase 
－ [tutorial: https://docs.djangoproject.com/en/1.10/topics/testing/](https://docs.djangoproject.com/en/1.10/topics/testing/)
- fixtures
``` text
商城API测试用户账号： xiaolu / test 
测试用户信息位于： flashsale/pay/fixtures/test.flashsale.customer.json
测试数据: python manage.py dumpdata items.Product --pks=[pk1,pk2] --indent=2 --format=json > app/fixtures/app.json 
```
- run test
``` shell
$ python manage.py test -t . -k 
```
- test coverage
`` shell
$ coverage run --omit="./ve/*" --source='.' manage.py test flashsale.restpro --keepdb
$ coverage report 
```

## Statsd 
- [tutorial: http://docs-ci.oneapm.com/api/python.html](http://docs-ci.oneapm.com/api/python.html)
``` code
# Counters:
from django_statsd.clients import statsd
statsd.incr('xiaolumm.prepay_count')
statsd.incr('xiaolumm.prepay_amount', sale_trade.payment)
# Gauges:
statsd.timing('users.online', 123)
statsd.timing('active.connections', 1001, tags=["protocol:http"])
```

## ApiRule
- 商城api url规范
``` text
/rest/v1[版本号]/portal[具体接口名称]
get请求: 直接返回结果对象,如{'products':[{...}]}, 异常则直接抛出http状态码:　返回的信息{'detail':'错误描述'}
post请求: 请求参数使用正常表单提交数据类型，
返回值：成功 {'code':0, 'info':'success'}，错误 {'code':1, 'info':'错误描述'}
```
- 后台业务api url规范
``` text
apis/chain[业务模块名]/v1[版本号]/product[具体接口名称]
get请求: 直接返回结果对象,如{'products':[{...}]}, 异常则直接抛出http状态码:　返回的信息{'detail':'错误描述'}
post请求: 请求参数接受参数为json格式
返回值：成功 {'products':[{...}]}，异常则直接抛出http状态码:　返回的信息{'detail':'错误描述'}
```

## DB Migrate 
- [tutorial: https://docs.djangoproject.com/en/1.8/topics/migrations/](https://docs.djangoproject.com/en/1.8/topics/migrations/)
- 原则
``` text
项目上线后：不能删除字段，只能新加字段替换原来字段的功能，原来字段保留；
```

## Logger 
- [tutorial: http://docs-ci.oneapm.com/api/python.html](http://docs-ci.oneapm.com/api/python.html)
``` code
现在日志分debug日志，跟业务统计日志两类，
debug日志的记录规则 需要分词地方使用逗号分隔, 如:
> logger.info('[func_name],[action],[id],[extra]')
> logger.error('[func_name],[action],[id],[exc_desc]', exc_info=True)

业务日志的记录方法是logger name 已 service开头：
import logging
json_logger = logging.getLogger('service.[业务名称]')
# action  记录类型必须要加上根据内部规划取名
json_logger.info({'action':'click', 'name':'meron', 'age':'20', 'ip':'192.0.0.1'})
(如果业务字段差异比较大，需要分不同日志logger)
```

## Merge
```
git pull　--rebase remote remote-branch
# same as:
git fetch remote remote-branch
git rebase remote/remote-branch
```


