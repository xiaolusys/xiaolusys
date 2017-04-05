# encoding=utf8
import shlex
import tempfile
from subprocess import Popen, PIPE
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def group_required(groups):
    def decorator(func):
        def wrapper(req, *args, **kwargs):
            user = req.user
            in_group = user.groups.filter(id__in=groups).first()
            if in_group or user.is_superuser:
                return func(req, *args, **kwargs)
            return HttpResponseForbidden()
        return wrapper
    return decorator

@login_required
@group_required([6])
def index(req):
    if req.method == 'POST':
        code = req.POST.get('code')
        # args = shlex.split(code)
        tf = tempfile.mkstemp()
        path = tf[1]

        print path

        with open(path, 'w+') as f:
            f.write(code)

        p = Popen(['python', path], stdout=PIPE, stdin=PIPE)
        out, err = p.communicate()

    return render(req, 'yunying/shell/index.html', locals())