from django.db import models
from jsonfield import JSONField
from jsonfield.fields import JSONCharFormField

class BaseModel(models.Model):
    status = models.BooleanField(default=True) #False delete,True exist,

    class Meta:
        abstract = True
  



class JSONCharMyField(JSONField,models.CharField):
    form_class = JSONCharFormField
