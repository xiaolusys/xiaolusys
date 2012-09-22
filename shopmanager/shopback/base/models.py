from django.db import models


#records status
UNEXECUTE = 'unexecute'
EXECERROR = 'execerror'
SUCCESS = 'success'
NORMAL = 'normal'
DELETE = 'delete'

class BaseModel(models.Model):
    status = models.BooleanField(default=True) #False delete,True exist,

    class Meta:
        abstract = True
  