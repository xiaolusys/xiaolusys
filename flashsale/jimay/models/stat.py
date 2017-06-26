# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models

class JimayAgentStat(models.Model):

    agent = models.OneToOneField('jimay.JimayAgent', related_name='agent_stat', verbose_name='己美代理')

    direct_invite_num = models.IntegerField(default=0, verbose_name='直接发展代理数量')
    indirect_invite_num = models.IntegerField(default=0, verbose_name='间接发展代理数量', help_text='所有下级代理的发展的总人数')

    direct_sales = models.IntegerField(default=0, verbose_name='直接销售额', help_text='自己下单的金额')
    indirect_sales = models.IntegerField(default=0, verbose_name='间接销售额', help_text='所有下级代理下单的总金额')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, db_index=True, verbose_name='修改时间')

    class Meta:
        db_table = 'jimay_agentstat'
        app_label = 'jimay'
        verbose_name = '己美医学/运营统计'
        verbose_name_plural = '己美医学/运营统计'

    def __unicode__(self):
        return '%s,%s' % (self.id, self.agent)

    @classmethod
    def calc_direct_invite_num_by_agent(cls, agent):
        from .agent import JimayAgent
        agent_stat, state = JimayAgentStat.objects.get_or_create(
            agent=agent
        )
        sub_agents = JimayAgent.objects.filter(parent_agent_id=agent.id)
        agent_stat.direct_invite_num = sub_agents.count()
        agent_stat.save(update_fields=['direct_invite_num'])

    @classmethod
    def calc_indirect_invite_num_by_agent(cls, agent):
        from .agent import JimayAgent
        agent_stat, state = JimayAgentStat.objects.get_or_create(
            agent=agent
        )

        sub_agents = JimayAgent.objects.filter(parent_agent_id=agent.id)
        direct_invite_num = 0
        if sub_agents.exists():
            sub_agent_ids = list(sub_agents.values_list('id', flat=True))
            sub_sub_agents = JimayAgent.objects.filter(parent_agent_id__in=sub_agent_ids)
            sub_sub_agent_ids = list(sub_sub_agents.values_list('id', flat=True))

            sub_agents_agg = JimayAgentStat.objects.filter(agent__in=sub_sub_agent_ids)\
            .aggregate(models.Sum('direct_invite_num'), models.Sum('indirect_invite_num'))
            print 'sub_agents_agg',sub_agents_agg
            direct_invite_num =  (
                (sub_agents_agg['direct_invite_num__sum'] or 0) +
                (sub_agents_agg['indirect_invite_num__sum'] or 0)
            )

        agent_stat.indirect_invite_num = direct_invite_num
        agent_stat.save(update_fields=['indirect_invite_num'])

        if agent.parent_agent:
            cls.calc_indirect_invite_num_by_agent(agent.parent_agent)
