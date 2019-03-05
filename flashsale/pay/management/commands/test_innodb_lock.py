# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand
from django.conf import settings
import time
from django.db import transaction
from flashsale.pay.models import Register


class Command(BaseCommand):
	def add_arguments(self, parser):
        # Positional arguments
		parser.add_argument('order_id', nargs='+', type=str)
		parser.add_argument('atomic_lock', nargs='+', type=str)
		parser.add_argument('lock_seconds', nargs='+', type=str)

	def handle(self, *args, **options):
		order_id = options.get('order_id') and options.get('order_id')[0]
		atomic_lock  = options.get('atomic_lock') and options.get('atomic_lock')[0]
		lock_seconds = options.get('lock_seconds') and options.get('lock_seconds')[0]
		if not order_id or not order_id.isdigit():
			print 'usage: python test_innodb_lock <order_id> [<do_lock>] [<lock_seconds>]'
			return

		print 'test start:', order_id, atomic_lock, lock_seconds
		if atomic_lock == '1':
			for i in range(100):
		with transaction.atomic():
			so = Register.objects.select_for_update().get(id=order_id)
			print 'atomic_lock wait:', so, lock_seconds 
			time.sleep(int(lock_seconds))
			so.verify_code = lock_seconds
			so.save()

			rg = Register.objectsrg = .get(id=order_id)

		else:
			so = Register.objects.get(id=order_id)
			so.verify_code = lock_seconds
			for i in range(300):
				print 'not atomic_lock ', so
				so.save()
				time.sleep(1)

		print 'test end'





