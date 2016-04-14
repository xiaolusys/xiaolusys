# coding=utf-8
"""
扫描项目目录的所有信号
"""
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand
from django.conf import settings
import os, sys
import re


def get_py_file(file_name):
    """如果是py文件返回文件名否则返回空"""
    if file_name.endswith('.py'):
        return file_name
    else:
        return None


def fun(path):
    """获取指定路径下的所有py文件路径"""
    file_list = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            file_path = root + '/' + fn
            if get_py_file(file_name=file_path):
                file_list.append(file_path)
    return file_list


def get_current_path():
    """获取执行命令的当前文件夹"""
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)


def signal_files_judge(file_path):
    """匹配出有信号的文件"""
    with open(file_path) as f:
        input = f.read()
        # output = re.search(input)


HAS_SIGNALS_FILES_PATH = set()

from django.db.models.signals import post_save


class Command(BaseCommand):
    def handle(self, *args, **options):
        """ 搜集项目中的信号到文件 """

        # path = get_current_path()
        # print "搜索路径为: %s" % path
        # files_list = fun(path)
        # print "项目中的py文件个数有: %s" % len(files_list)
        # print "信号文件搜索前: ", HAS_SIGNALS_FILES_PATH
        # map(signal_files_judge, files_list)
        # print "搜索成功... %s 含有信号的文件为: ", HAS_SIGNALS_FILES_PATH

        apps = settings.INSTALLED_APPS
        b = post_save.receivers[80]
        x = b[1]
        print x
        print '功能文档：', x.__doc__

        for app in apps:
            try:
                exec ('from ' + app + ' import signals')
                print "---------", app
            except ImportError:
                # return
                pass
                # print app + 'has not signals models'

