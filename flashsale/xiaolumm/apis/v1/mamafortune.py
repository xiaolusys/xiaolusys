# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging

logger = logging.getLogger(__name__)


def get_mama_fortune_by_mama_id(mama_id):
    # type: (int) -> MamaFortune
    from ...models import MamaFortune
    return MamaFortune.objects.get(mama_id=mama_id)
