# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

import datetime
from collections import defaultdict

from django.db import connections
from flashsale.xiaolumm.models import XiaoluMama, ReferalRelationship, MamaReferalTree


def recursive_appendchilds(node, node_maps, gradient):
    copy_node = node.copy()
    copy_node.update({
        'direct_invite_num': 0,
        'indirect_invite_num': 0,
        'gradient': gradient,
    })
    child_nodes = node_maps.get(copy_node['referal_to_mama_id'])
    copy_node.setdefault('childs', [])
    if not child_nodes:
        return copy_node

    for child_node in child_nodes:
        child_node = recursive_appendchilds(child_node, node_maps, gradient + 1)
        copy_node['childs'].append(child_node)

    copy_node['direct_invite_num'] = len(copy_node['childs'])
    copy_node['indirect_invite_num'] = sum([c['indirect_invite_num'] + c['direct_invite_num'] for c in copy_node['childs']])
    return copy_node


def get_referalrelationship_maps():
    referals = ReferalRelationship.objects.filter(
        referal_type__gte=XiaoluMama.ELITE, status=ReferalRelationship.VALID).order_by('referal_from_mama_id')
    referals_value = referals.values('referal_to_mama_id', 'referal_from_mama_id')

    tree_nodes = defaultdict(list)
    for referal in referals_value:
        tree_nodes[referal['referal_from_mama_id']].append(referal)

    return tree_nodes


def save_mama_referal_trees(tree_nodes):
    childs = tree_nodes.pop('childs')
    mama_id = tree_nodes.get('referal_to_mama_id')
    try:
        mama_referal = MamaReferalTree.objects.filter(referal_to_mama_id=mama_id).first()
        if not mama_referal:
            mama_referal = MamaReferalTree(referal_to_mama_id=mama_id)
        for k, v in tree_nodes.iteritems():
            setattr(mama_referal, k, v)
        mama_referal.save()
    except Exception, exc:
        print 'exc:', exc, tree_nodes

    for node in childs:
        save_mama_referal_trees(node)


class Command(BaseCommand):

    def handle(self, *args, **options):
        sql = """
            SELECT
                distinct fr.referal_from_mama_id
            FROM
                flashsale_xlmm_referal_relationship fr
                    LEFT JOIN
                flashsale_xlmm_referal_relationship xr
                    ON fr.referal_from_mama_id = xr.referal_to_mama_id
            WHERE
                fr.referal_type >= %s AND (xr.referal_from_mama_id IS NULL or xr.referal_type < %s);
            """%(XiaoluMama.ELITE, XiaoluMama.ELITE)

        cursor = connections['default'].cursor()
        cursor.execute(sql)
        mama_ids = cursor.fetchall()
        print 'fetch mama top ids:', datetime.datetime.now()

        referal_maps = get_referalrelationship_maps()
        print 'genarate mama referal maps:', datetime.datetime.now()

        count = 0
        for parent_mama_id  in mama_ids:
            referal_treenodes = recursive_appendchilds(
                {
                    'referal_from_mama_id': 0,
                    'referal_to_mama_id': parent_mama_id[0],
                    'direct_invite_num': 0,
                    'indirect_invite_num': 0
                },
                referal_maps,
                0
            )
            save_mama_referal_trees(referal_treenodes)
            count += 1
            if count % 100 == 0:
                print 'save mama referal count:', count, datetime.datetime.now()

        cursor.close()

