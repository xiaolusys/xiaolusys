# coding=utf-8
"""
扫描项目目录的所有信号
"""
__author__ = 'jishu_linjie'
import os, sys
import re
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save


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
            if not fn.startswith('signals.'):
                continue
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


def find_file_signals(file_path):
    """ 匹配出所有信号 """
    # r = '[\w_]*signal[a-zA-Z0-9_]*'
    r = '[\w_]+\s*=\s*Signal\('
    signals_set = set()
    with open(file_path) as f:
        file_lines = f.readlines()
    for line in file_lines:
        if line:
            signals_set.add(re.match(r, line))
    try:
        signals_set.remove(None)
    except KeyError:
        return signals_set
    return signals_set


def handler_recivers_result(target_signal, results):
    """
    command: import path and the signal
    results: signal receivers
    """
    receiver_function = []
    r = '\([\w_]*\)'
    for i in results:
        str_xxx = str(i[1])
        if 'function' in str_xxx:
            function = re.search(r, str_xxx)
            if function:
                f = function.group()
                func_name = f.replace("(", "").replace(")", '')
                receiver_function.append(func_name)

    return {"signal": target_signal, "receiver_functions": receiver_function}


class Command(BaseCommand):
    def handle(self, *args, **options):
        """ 搜集项目中的信号到文件 """
        path = get_current_path()
        print "搜索路径为: %s" % path
        files_list = fun(path)
        print "项目中的signals*.py文件个数有: %s" % len(files_list)
        all_signals = []
        for fl in files_list:
            signals_set = find_file_signals(fl)
            if signals_set:
                xxx = fl.split('xiaolusys/shopmanager')[1][1::][:-3]
                xxxx = xxx.replace('/', '.')
                li = []
                for i in signals_set:
                    li.append(i.group().replace('Signal(', '').replace('=', '').replace(' ', ''))
                all_signals.append({xxxx: li})
        # print all_signals
        data = []
        for file_signal in all_signals:
            key = file_signal.keys()[0]
            value = file_signal[key]
            for s in value:
                command = 'from ' + key + ' import ' + s
                # print "执行语句：%s" % command
                try:
                    exec (command)
                except ImportError:
                    print "%s 模块不存在" % command
                receivers_command = s + '.receivers'
                # print "执行receivers命令:%s" % receivers_command
                results = eval(receivers_command)
                signal_funcs = handler_recivers_result(command, results)
                data.append(signal_funcs)

        results1 = post_save.receivers
        signal_funcs = handler_recivers_result('post_save', results1)
        data.append(signal_funcs)

        results2 = post_delete.receivers
        signal_funcs = handler_recivers_result('post_delete', results2)
        data.append(signal_funcs)

        results3 = pre_save.receivers
        signal_funcs = handler_recivers_result('pre_save', results3)
        data.append(signal_funcs)

        results4 = pre_delete.receivers
        signal_funcs = handler_recivers_result('pre_delete', results4)
        data.append(signal_funcs)

        with open('collect_signals.json', 'w') as f:
            f.write(str(data))



