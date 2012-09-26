from django import template

register = template.Library()

@register.filter(name='format_dt')  
def format_dt(dt): 
    print dt  
    return '%s%d,%s'%('周',dt.date().isoweekday(),dt.strftime("%H时%M分"))  