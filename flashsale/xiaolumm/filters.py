# coding=utf-8
from django.contrib.auth.models import User
from django.contrib.admin import SimpleListFilter
from .models import XiaoluMama, CashOut


########################################################################
class UserNameFilter(SimpleListFilter):
    """"""
    title = u'管理员'
    parameter_name = 'username'

    def lookups(self, request, model_admin):
        # xiaolumm_xiaolumama(id,user_group_id )   xiaolumm_cashout(xlmm)  shop_weixin_group(name)
        manager_list = []
        managers = XiaoluMama.objects.values('manager').distinct()
        for mgr in managers:
            try:
                duser = User.objects.get(id=mgr['manager'])
            except User.DoesNotExist:
                pass
            else:
                manager_list.append((str(duser.id), duser.username))
        return tuple(manager_list)

    def queryset(self, request, queryset):
        mgr_id = self.value()
        if not mgr_id:
            return queryset
        else:
            cash_rawqs = CashOut.objects.raw(
                "select xc.id from xiaolumm_cashout xc LEFT JOIN xiaolumm_xiaolumama xx on xc.xlmm = xx.id where xc.status = '{0}' and xx.manager = '{1}' ".format(
                    CashOut.PENDING, mgr_id))
            cash_ids = [cs.id for cs in cash_rawqs]
            # return CashOut.objects.filter(id__in=cash_ids)
            return queryset.filter(id__in=cash_ids)
