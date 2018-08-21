# coding=utf-8
from __future__ import unicode_literals,absolute_import

from django.shortcuts import render
from django.http import HttpResponse


def return_tuihuo_html(request):
    # return HttpResponse("123")
    return render(request, "dinghuo/change_form.html")