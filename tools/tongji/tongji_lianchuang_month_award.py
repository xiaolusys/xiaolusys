# coding: utf8
from __future__ import absolute_import, unicode_literals

import os, sys
import copy
import datetime
import calendar
import xlrd
import json

from pyExcelerator import *
import csv

from collections import defaultdict

flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]

def pre_year_month(year, month):
    if month == 1:
        return year - 1, 12
    return year , month - 1

#####################################
# {
#     "夏夏":{
#         "data":{
#             "jjpingtui":0,
#             "salenum":0,
#             "tuandui":0,
#             "zjpingtui":0
#         },
#         "child":{
#
#         }
#     },
#     "桃夭":{
#         "data":{
#             "jjpingtui":0,
#             "salenum":0,
#             "tuandui":0,
#             "zjpingtui":0
#         },
#         "child":{
#             "文芳":{
#                 "data":{
#                     "jjpingtui":0,
#                     "salenum":0,
#                     "tuandui":0,
#                     "zjpingtui":0
#                 },
#                 "child":{
#
#                 }
#             }
#         }
#     }
# }
#####################################

dd = {
    "data":{
        "is_direct": True,  #
        "private_num": 0,   # 个人业绩
        "zjpingtui_num": 0, # 直接平推业绩
        "jjpingtui_num": 0, # 间接平推业绩
        "tuandui_num": 0,   # 团队业绩(含自己)
        "tuandui_amount": 0,  # 团队奖励金额
    },
    "child":{

    }
}

lcrl_month_list = [] # 联创月度奖励统计列表


def calc_team_award(purchase_num):
    """　团队业绩奖 """

    if purchase_num >= 40000:
        return 6 * purchase_num

    elif purchase_num >= 20000:
        return 5 * purchase_num

    elif purchase_num >= 10000:
        return 4 * purchase_num

    elif purchase_num >= 4000:
        return 3 * purchase_num

    return 0

def recursive_append_child(node, node_map, cs_map):
    node_value = copy.deepcopy(dd)
    child_nodes = node_map.get(node)
    node_value['data']['private_num'] = cs_map.get(node, 0)

    if child_nodes:
        for child_node in child_nodes:
            child_node_value = recursive_append_child(child_node, node_map, cs_map)
            node_value['child'][child_node] = child_node_value

    child_values = node_value['child'].values()
    # print 'child_values==============', child_values
    node_value['data']['zjpingtui_num'] = sum([k['data']['private_num'] for k in child_values])
    node_value['data']['jjpingtui_num'] = sum([k['data']['zjpingtui_num'] for k in child_values])
    node_value['data']['tuandui_num'] = cs_map.get(node, 0) + sum([k['data']['tuandui_num'] for k in child_values])

    node_value['data']['tuandui_amount'] = calc_team_award(node_value['data']['tuandui_num']) - \
         sum([calc_team_award(k['data']['tuandui_num']) for k in child_values])

    return node_value

def tree_node_2_map(tree_node, p_name, node_map):
    """ tree_node: {'A':{'data':{}, 'child':{}}, 'B':{'data':{}, 'child':{}}} """

    node_sorted = sorted(tree_node.items(), key=lambda k: k[1]['data']['tuandui_num'], reverse=True)
    for k_name, node_value in node_sorted:
        node_map[k_name] = copy.copy(node_value['data'])

        tree_node_2_map(node_value['child'], k_name, node_map)



def recursive_output_nodes1(p_name, n_name, node, output_list):
    """ p_name上级名称，　n_name当前代理名称， node节点数据 """
    data = node['data']
    ov = [n_name, p_name, data['private_num'], data['zjpingtui_num'] * 4, data['jjpingtui_num'] * 1, 0, data['tuandui_amount'], 0]
    output_list.append(ov)

    for c_name, child_node in node['child'].iteritems():
        recursive_output_nodes1(n_name, c_name, child_node, output_list)


def recursive_output_nodes2(p_name, node, node_map_serial, output_list, blank=True):
    """ p_name上级名称，　n_name当前代理名称， node节点数据 """

    for c_name, node_value in node.iteritems():
        ov = [
            c_name,
            p_name,
            sum([d[c_name]['private_num'] if d.get(c_name, None) else 0  for d in node_map_serial]),
            sum([d[c_name]['zjpingtui_num'] if d.get(c_name, None) else 0 for d in node_map_serial]) * 4,
            sum([d[c_name]['jjpingtui_num'] if d.get(c_name, None) else 0 for d in node_map_serial]) * 1,
            0,
            sum([d[c_name]['tuandui_amount'] if d.get(c_name, None) else 0 for d in node_map_serial]),
            0
        ]
        output_list.append(ov)

        recursive_output_nodes2(c_name, node_value['child'], node_map_serial, output_list, blank=False)

        if blank:
            output_list.append([""])



def calc_month_stat(chg_file, month_dt):
    """ 统计联创的月订货业绩 """
    cs_map = {}
    chg_data = xlrd.open_workbook(chg_file)
    chg_table = chg_data.sheets()[0]

    chg_nrows = chg_table.nrows
    for i in range(1, chg_nrows):
        row = chg_table.row_values(i)
        if row[15].strip()[0:7] != month_dt:
            continue
        name, mobile, charge = row[1].strip(), row[2].strip(), row[6]
        k_name = '%s(%s****%s)' % (name, mobile[0:3], mobile[7:11])
        cs_map[k_name] = cs_map.get(k_name, 0) + int(charge / 86)

    return cs_map


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print >> 'python tongji_lianchuang_month_award <relationship_file> <chargerecord_file> <month_date>'
        exit()

    rls_file  = sys.argv[1]
    chg_file = sys.argv[2]
    month_dt = sys.argv[3]

    # 提取用户关系数据
    rls_data = xlrd.open_workbook(rls_file)
    rls_table = rls_data.sheets()[0]

    rls_nrows = rls_table.nrows
    rl_map_nodes = defaultdict(list)
    for i in range(1, rls_nrows):
        master, invitor = rls_table.row_values(i)[0:2]
        rl_map_nodes[master].append(invitor)

    # 获取顶级联创列表
    top_keys = set(rl_map_nodes.keys()) - set(flatten(rl_map_nodes.values()))

    # 计算过去 12个月的联创团队订货业绩
    year, month = [int(i) for i in month_dt.split('-')]
    for m in range(0, 12):

        m_dt = '%4d-%02d' % (year, month)
        cs_map = calc_month_stat(chg_file, m_dt)

        rl_map = {}
        rl_map_nodes_copy = copy.deepcopy(rl_map_nodes)
        for t_key in top_keys:
            rl_map[t_key] = recursive_append_child(t_key, rl_map_nodes_copy, cs_map)

        lcrl_month_list.append(rl_map)
        year, month = pre_year_month(year, month)

    first_month_node_map = lcrl_month_list[0]

    for index, value in enumerate(lcrl_month_list):
        node_map = {}
        tree_node_2_map(value, '总部', node_map)
        lcrl_month_list[index] = node_map

    sheet_name_list = [('月累计', 1), ('季累计', 3), ('半年累计', 6), ('年累计', 12)]
    sheet_title_list= [
        "联创",
        "上级联创",
        "累计订货数（盒）",
        "直接平推奖励（元）",
        "间接平推奖励（元）",
        "个人业绩奖（元）",
        "团队奖励（元）",
        "合计（元）"
    ]

    # 数据表单项组装
    sheet_award_list = []
    year, month = [int(i) for i in month_dt.split('-')]
    for sheet_name, month_num in sheet_name_list:
        turn_back_year = month_num - 1 >= month
        m_start = [year - 1 if turn_back_year else year, 13 + month - month_num if turn_back_year else month - month_num + 1]
        m_end   = [year, month]

        row_list = []
        row_list.append(["%4d年%2d月~%4d年%2d月联创团队%s业绩奖励" % tuple(m_start + m_end + [sheet_name])])
        row_list.append(sheet_title_list)

        recursive_output_nodes2('总部', first_month_node_map, lcrl_month_list[0:month_num], row_list)

        row_list.append(["分类汇总"])

        sheet_award_list.append((sheet_name, row_list))

    # 生成xls文件
    wb = Workbook()
    for sheet_name, row_list in sheet_award_list:
        ws = wb.add_sheet(sheet_name)
        for i, row in enumerate(row_list):
            for j, s in enumerate(row):
                ws.write(i, j, s)

    wb.save('/tmp/month_award_%s.xls' % month_dt)















