# coding: utf-8
from django.db.models.signals import pre_save, post_save


def update_model_fields(obj, update_fields=[], trigger_signals=False):
    """
        根据给定字段，保存该对象的对应字段信息
    """
    field_entry = {}
    for k in update_fields:
        if hasattr(obj, k):
            field_entry[k] = getattr(obj, k)

    if trigger_signals:
        pre_save.send(sender=obj.__class__, instance=obj)
    rows = obj.__class__.objects.filter(pk=obj.pk).update(**field_entry)
    if trigger_signals:
        post_save.send(sender=obj.__class__, instance=obj)
    return rows


def update_model_change_fields(obj, update_params={}, trigger_signals=False):
    """
        只更新在obj上发生改变的属性值
    """
    field_entry = {}
    for k, v in update_params.iteritems():
        if hasattr(obj, k) and getattr(obj, k) != v:
            field_entry[k] = v
            setattr(obj, k, v)

    if not field_entry:
        return 0
    if trigger_signals:
        pre_save.send(sender=obj.__class__, instance=obj)
    rows = obj.__class__.objects.filter(pk=obj.pk).update(**field_entry)
    if trigger_signals:
        post_save.send(sender=obj.__class__, instance=obj)
    return rows


def get_class_fields(modelclass):
    return [f.column for f in modelclass._meta.fields]
