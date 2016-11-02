from django.db import models
from django.conf import settings
from django.db.backends.mysql.creation import DatabaseCreation


# DatabaseCreation.data_types['AutoField'] = 'bigint(20) AUTO_INCREMENT'

class BigIntegerAutoField(models.AutoField):
    description = "BigInteger field that auto increments"

    def db_type(self, connection):
        return 'bigint(20) auto_increment'


# if settings.DEBUG:
#    BigIntegerAutoField = models.AutoField


class TimestampField(models.Field):
    description = 'simple Timestamp field for MYSQL'

    def db_type(self, connection):
        return 'TIMESTAMP default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP'


class BigIntegerForeignKey(models.ForeignKey):
    description = "BigInteger foreignkey"

    def db_type(self, connection):
        rel_field = self.rel.get_related_field()
        if (isinstance(rel_field, models.AutoField) or
                (not connection.features.related_fields_match_type and
                     isinstance(rel_field, (models.PositiveIntegerField,
                                            models.PositiveSmallIntegerField)))):
            return models.BigIntegerField().db_type(connection=connection)
        return rel_field.db_type(connection=connection)
