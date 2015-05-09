from django.contrib import admin


from .models import StatisticsShopping, StatisticsShoppingByDay




class StatisticsShoppingAdmin(admin.ModelAdmin):
    list_display = ('linkid', 'linkname', 'openid', 'wxorderid', 'wxorderamount','tichengcount','shoptime')
    list_filter = ('linkid',)
    search_fields = ['linkid', 'openid']

admin.site.register(StatisticsShopping, StatisticsShoppingAdmin)
admin.site.register(StatisticsShoppingByDay)