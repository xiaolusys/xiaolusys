#-*- coding:utf8 -*-


def update_model_fields(obj,update_fields=[]):
    """ 
        根据给定字段，保存该对象的对应字段信息
    """
    field_entry = {}
    for k in update_fields:
       if hasattr(obj,k) :
           field_entry[k] = getattr(obj,k)
    
    rows = obj.__class__.objects.filter(pk=obj.pk).update(**field_entry)
    return rows