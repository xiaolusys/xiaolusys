from django.db import models


class BaseModel(models.Model):
    status = models.BooleanField(default=True)  # False delete,True exist,

    class Meta:
        abstract = True
