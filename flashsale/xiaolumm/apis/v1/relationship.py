# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging

logger = logging.getLogger(__name__)

__ALL__ = [
    'get_relationship_by_mama_id'
]


def get_relationship_by_mama_id(mamaid):
    # type: (int) -> Optional[ReferalRelationship]
    from ...models import ReferalRelationship

    return ReferalRelationship.objects.filter(referal_to_mama_id=mamaid, status=ReferalRelationship.VALID).first()

