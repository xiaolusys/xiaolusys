# coding=utf-8
# __author__ = 'linjie'
from django.conf.urls.defaults import patterns, include, url
from .view import popularize_Cost
from django.contrib.admin.views.decorators import staff_member_required
from view_repeat_stats import StatsRepeatView, StatsSaleView


urlpatterns = patterns('',
                       url(r'^popu_cost/', popularize_Cost, name="popularize_Cost"),
                       url(r'^stats_repeat/$', staff_member_required(StatsRepeatView.as_view()), name="stats_repeat"),
                       url(r'^stats_sale/$', staff_member_required(StatsSaleView.as_view()), name="stats_sale"),
                       )
