from django.db import models, connections
from django.db.models.query import QuerySet
from core.ormcache.managers import CacheManager

class ApproxCountQuerySet(QuerySet):
    def count(self):
        '''
        Override entire table count queries only. Any WHERE or other altering
        statements will default back to an actual COUNT query.
        '''
        if self._result_cache is not None and not self._iter:
            return len(self._result_cache)

        is_mysql = 'mysql' in connections[self.db].client.executable_name.lower()

        query = self.query
        if (is_mysql and not query.where and
                    query.high_mark is None and
                    query.low_mark == 0 and
                not query.select and
                not query.group_by and
                not query.having and
                not query.distinct):
            # If query has no constraints, we would be simply doing
            # "SELECT COUNT(*) FROM foo". Monkey patch so the we
            # get an approximation instead.
            cursor = connections[self.db].cursor()
            cursor.execute("SHOW TABLE STATUS LIKE %s",
                           (self.model._meta.db_table,))
            return cursor.fetchall()[0][4]
        else:
            return self.query.get_count(using=self.db)


class BaseManager(models.Manager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set


# from tagging.models import TaggedItem
# from tagging.utils import  get_tag_list
#
# class BaseTagManager(BaseManager):
#
#     def add_tags_to_object_or_list(self, qs, tags):
#         object_list = qs
#         if not isinstance(qs, (QuerySet, list, tuple)):
#             object_list = [qs]
#
#         tag_list = get_tag_list(tags)
#         tag_set = set(tag_list)
#         for obj in object_list:
#             obj_tag_set = set(obj.tags.split())
#             obj.tags    = ' '.join(obj_tag_set + tag_set)
#             obj.save(update_fields=['tags'])
#
#
#     def remove_tags_from_object_or_list(self, qs, tags):
#         object_list = qs
#         if not isinstance(qs, (QuerySet, list, tuple)):
#             object_list = [qs]
#
#         tag_list = get_tag_list(tags)
#
#         tag_set = set(tag_list)
#         for obj in object_list:
#             obj_tag_set = set(obj.tags.split())
#             obj.tags = ' '.join(obj_tag_set - tag_set)
#             obj.save(update_fields=['tags'])
#
#     def has_tag_for_obj(self, obj, tag):
#         tag_list = obj.tags.split()
#         return tag in tag_list
#
#     def get_mix_queryset_by_tags(self, tags, queryset=None):
#         tag_list = get_tag_list(tags)
#
#         model_object = queryset or self.all()
#         qs = TaggedItem.objects.get_by_model(model_object, tag_list)
#         return qs
#
#     def get_union_queryset_by_tags(self, tags, queryset=None):
#         tag_list = get_tag_list(tags)
#
#         model_object = queryset or self.all()
#         qs = TaggedItem.objects.get_union_by_model(model_object, tag_list)
#         return qs