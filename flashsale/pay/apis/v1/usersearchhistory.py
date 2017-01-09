# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging

logger = logging.getLogger(__name__)

__ALL__ = [
    'create_user_search_history',
    'get_distinct_user_search_product_history_by_user_id',
    'clear_user_search_history',
]

from ...models import UserSearchHistory


def get_distinct_user_search_product_history_by_user_id(user_id):
    # type: (int) -> Optional[List[UserSearchHistory]]
    """更具用户id 获取该用户  特卖款式 搜索历史 记录
    """
    xs = UserSearchHistory.objects.filter(user_id=user_id,
                                          target=UserSearchHistory.MODEL_PRODUCT,
                                          status=UserSearchHistory.NORMAL).order_by('-created')
    hs = []
    content = set()
    for x in xs:
        if x.content in content:
            continue
        else:
            hs.append(x)
        content.add(x.content)
    return hs


def create_user_search_history(content, target, user_id=0, result_count=0):
    # type: (text_type, text_type, int, int) -> UserSearchHistory
    """创建用户搜索历史 记录
    """
    h = UserSearchHistory(user_id=user_id,
                          content=content,
                          target=target,
                          result_count=result_count)
    h.save()
    return h


def clear_user_search_history(user_id, target):
    # type: (int, text_type) -> bool
    """清楚用户指定的 搜索历史记录
    """
    UserSearchHistory.objects.filter(user_id=user_id,
                                     target=target,
                                     status=UserSearchHistory.NORMAL).update(status=UserSearchHistory.CLEAR_BY_USER)
    return True
