from django.db import models
from django.utils.translation import ugettext as _

# Create your models here.
class County(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)

class Municipality(models.Model):
    county = models.ForeignKey(County, verbose_name=_('County'))
    name = models.CharField(_('Name'), max_length=100)

class Location(models.Model):
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, verbose_name=_('County'))
    municipality = models.ForeignKey(Municipality,
            verbose_name=_("Municipality"))
