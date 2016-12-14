# encoding=utf8
import shlex
import tempfile
from subprocess import Popen, PIPE
from django.shortcuts import render


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