# coding: utf8
from __future__ import absolute_import, unicode_literals

import os
import sys
import copy
import datetime


dsa = {
    "members": {
        "2017-10": 0,
        "2017-11": 0,
        "2017-12": 0,
        "2018-01": 0,
        "2018-02": 0,
    },
    "sales": {
        "2017-10": 0,
        "2017-11": 0,
        "2017-12": 0,
        "2018-01": 0,
        "2018-02": 0,
    }
}

dsc = {
    "联创": copy.deepcopy(dsa),
    "总代": copy.deepcopy(dsa),
    "省代": copy.deepcopy(dsa),
    "市代": copy.deepcopy(dsa),
    "特约": copy.deepcopy(dsa),
}


ds = {}

def parse_csvdata(file_path):
    # format only csv file
    global ds
    f = open(file_path, 'r')
    lines = f.readlines()
    f.close()

    ga = []
    gb = []
    gc = []
    gd = []
    ge = []

    pre_head_name = ''
    pre_gp_mth = ''
    for l in lines[1:]: # exclude first line
        ss = l.split(',')
        head_name = ss[0].strip()

        if pre_head_name and not head_name.startswith('|') and (ga or gb or gc or gd or ge):
            ds[pre_head_name]["联创"]["members"][pre_gp_mth] = len(ga)
            ds[pre_head_name]["联创"]["sales"][pre_gp_mth] = sum(ga)
            ds[pre_head_name]["总代"]["members"][pre_gp_mth] = len(gb)
            ds[pre_head_name]["总代"]["sales"][pre_gp_mth] = sum(gb)
            ds[pre_head_name]["省代"]["members"][pre_gp_mth] = len(gc)
            ds[pre_head_name]["省代"]["sales"][pre_gp_mth] = sum(gc)
            ds[pre_head_name]["市代"]["members"][pre_gp_mth] = len(gd)
            ds[pre_head_name]["市代"]["sales"][pre_gp_mth] = sum(gd)
            ds[pre_head_name]["特约"]["members"][pre_gp_mth] = len(ge)
            ds[pre_head_name]["特约"]["sales"][pre_gp_mth] = sum(ge)

        if not head_name:
            continue

        if not head_name.startswith('|') and head_name not in ds:
            ds[head_name] = copy.deepcopy(dsc)

        if not head_name.startswith("|"):
            pre_head_name = head_name
            pre_gp_mth = ss[9].strip()
            ga = []
            gb = []
            gc = []
            gd = []
            ge = []


        gp_name  = ss[2].strip()
        ps_sales = ss[7].strip()

        if gp_name == "联创":
            ga.append(int(ps_sales) / 86)
        elif gp_name == "总代":
            gb.append(int(ps_sales) / 99)
        elif gp_name == "省代":
            gc.append(int(ps_sales) / 118)
        elif gp_name == "市代":
            gd.append(int(ps_sales) / 138)
        elif gp_name == "特约":
            ge.append(int(ps_sales) / 165)

    if pre_head_name and (ga or gb or gc or gd or ge):
        ds[pre_head_name]["联创"]["members"][pre_gp_mth] = len(ga)
        ds[pre_head_name]["联创"]["sales"][pre_gp_mth] = sum(ga)
        ds[pre_head_name]["总代"]["members"][pre_gp_mth] = len(gb)
        ds[pre_head_name]["总代"]["sales"][pre_gp_mth] = sum(gb)
        ds[pre_head_name]["省代"]["members"][pre_gp_mth] = len(gc)
        ds[pre_head_name]["省代"]["sales"][pre_gp_mth] = sum(gc)
        ds[pre_head_name]["市代"]["members"][pre_gp_mth] = len(gd)
        ds[pre_head_name]["市代"]["sales"][pre_gp_mth] = sum(gd)
        ds[pre_head_name]["特约"]["members"][pre_gp_mth] = len(ge)
        ds[pre_head_name]["特约"]["sales"][pre_gp_mth] = sum(ge)



def execute(dir_path):

    global ds
    for x in os.listdir(dir_path):
        file_path = dir_path + '/' + x
        print '============file_path===========', file_path
        if os.path.isfile(file_path):
            parse_csvdata(file_path)

    gp_orders = ["联创","总代","省代","市代","特约"]

    import json
    print json.dumps(ds['刘艳'], indent=2)

    import csv
    with open('/home/meron/Desktop/rps_%s.csv' % datetime.datetime.strftime(datetime.date.today(), '%Y%m%d'), 'wb') as cvf:
        spamwriter = csv.writer(cvf, dialect='excel')
        for gp_name, gp_data in ds.iteritems():
            frt_line = ["团队名称","联创","","","","","","总代","","","","","","省代","","","","","","市代","","","","","","特约","","","","",""]

            scd_line = [gp_name]
            key_list = gp_data.items()[0][1]["members"].keys()
            key_list.sort()
            key_list.insert(0, "月份")
            for i in range(1, 6):
                scd_line.extend(copy.deepcopy(key_list))

            thd_line = [""]
            for gpo in gp_orders:
                member_list = sorted(gp_data[gpo]["members"].items(), key=lambda x:x[0])
                member_list = [str(d[1]) for d in member_list]
                member_list.insert(0, "人数")
                thd_line.extend(member_list)

            fth_line = [""]
            for gpo in gp_orders:
                sale_list = sorted(gp_data[gpo]["sales"].items(), key=lambda x: x[0])
                sale_list = [str(d[1]) for d in sale_list]
                sale_list.insert(0, "业绩")
                fth_line.extend(sale_list)

            spamwriter.writerow(frt_line)
            spamwriter.writerow(scd_line)
            spamwriter.writerow(thd_line)
            spamwriter.writerow(fth_line)
            spamwriter.writerow([])

if __name__ == "__main__":
    """ input command: python tongji_daili_shuliang_yeji """
    execute("./data/yeji")


