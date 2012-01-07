from django.db import models
from django.conf import settings


class BigIntegerAutoField(models.AutoField):
    description = "BigInteger field that auto increments"
    def db_type(self, connection):
        return 'bigint(20) auto_increment'

if settings.DEBUG:
    BigIntegerAutoField = models.AutoField


class TimestampField(models.Field):
    description = 'simple Timestamp field for MYSQL'
    def db_type(self, connection):
        return 'TIMESTAMP default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP'
  