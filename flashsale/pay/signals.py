from django.dispatch import Signal

signal_saletrade_pay_confirm = Signal(providing_args=['obj'])

signal_saleorder_post_update = Signal(providing_args=['instance', 'created', 'raw'])

signal_saletrade_refund_confirm = Signal(providing_args=['obj'])

signal_saletrade_refund_post = Signal(providing_args=['obj'])

signal_record_supplier_models = Signal(providing_args=['obj'])
