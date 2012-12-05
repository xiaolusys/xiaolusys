from django.contrib import admin
from contry.models import Location,County,Municipality
from contry.forms import LocationForm

class LocationAdmin(admin.ModelAdmin):
    form = LocationForm
    class Media:
        js = ('http://ajax.googleapis.com/ajax/libs/jquery/1.4.0/jquery.min.js',
                '/static/municipality.js')

admin.site.register(Location, LocationAdmin)

class CountyAdmin(admin.ModelAdmin):
    list_display = ('id','name')
   

admin.site.register(County, CountyAdmin)


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('id','county','name')
   

admin.site.register(Municipality, MunicipalityAdmin)
