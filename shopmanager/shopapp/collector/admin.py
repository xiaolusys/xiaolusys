__author__ = 'meixqhi'
from django.contrib import admin
from shopapp.collector.models import ProductPageRank, ProductTrade


class ProductPageRankAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'item_id', 'title', 'user_id', 'nick', 'created', 'rank')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('month', 'day')
    search_fields = ['keyword', 'title', 'item_id', 'created']


admin.site.register(ProductPageRank, ProductPageRankAdmin)


class ProductTradeAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'user_id', 'nick', 'trade_id', 'num', 'price', 'trade_at', 'state')
    # list_editable = ('update_time','task_type' ,'is_success','status')

    list_filter = ('year', 'month', 'day', 'state')
    search_fields = ['item_id', 'user_id', 'nick', 'trade_id']


admin.site.register(ProductTrade, ProductTradeAdmin)
