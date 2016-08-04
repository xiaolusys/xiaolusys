from django.http import HttpResponse
from django.shortcuts import render

def wk(request):
    return render(request, 'push_image.html')