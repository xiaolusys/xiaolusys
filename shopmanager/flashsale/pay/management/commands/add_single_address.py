# coding=utf-8
__author__ = 'denghui'
from flashsale.pay.models.address import UserSingleAddress
from flashsale.pay.models import UserAddress
import hashlib
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        for i in UserAddress.objects.all():
            uni_key = i.receiver_state+i.receiver_city+i.receiver_district+i.receiver_address
            uni_key = hashlib.sha1(uni_key).hexdigest()
            if not UserSingleAddress.objects.filter(uni_key=uni_key).exists():
                UserSingleAddress.objects.create(uni_key=uni_key,created=i.created,modified=i.modified,receiver_state=i.receiver_state,receiver_city=i.receiver_city,receiver_district=i.receiver_district,receiver_address=i.receiver_address,receiver_zip=i.receiver_zip)
