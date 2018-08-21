import time
from django.http import HttpResponsePermanentRedirect
from django.db import connection
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from importlib import import_module
from django.contrib.sessions.middleware import SessionMiddleware

import logging
logger = logging.getLogger(__name__)


class XForwardedForMiddleware():
    def process_request(self, request):
        if request.META.has_key("HTTP_X_FORWARDED_FOR"):
            request.META["HTTP_X_PROXY_REMOTE_ADDR"] = request.META["REMOTE_ADDR"]
            parts = request.META["HTTP_X_FORWARDED_FOR"].split(",", 1)
            request.META["REMOTE_ADDR"] = parts[0]


class SecureRequiredMiddleware(object):
    def __init__(self):
        self.paths = getattr(settings, 'SECURE_REQUIRED_PATHS')
        self.enabled = self.paths and getattr(settings, 'HTTPS_SUPPORT')

    def process_request(self, request):
        if self.enabled and not request.is_secure():
            for path in self.paths:
                if request.get_full_path().startswith(path):
                    request_url = request.build_absolute_uri(request.get_full_path())
                    secure_url = request_url.replace('http://', 'https://')
                    return HttpResponsePermanentRedirect(secure_url)
        return None


class DisableDRFCSRFCheck(object):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


class QueryCountDebugMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """
    def process_response(self, request, response):
        if response.status_code == 200:
            total_time = 0
            for query in connection.queries:
                query_time = query.get('time')
                if query_time is None:
                    # django-debug-toolbar monkeypatches the connection
                    # cursor wrapper and adds extra information in each
                    # item in connection.queries. The query time is stored
                    # under the key "duration" rather than "time" and is
                    # in milliseconds, not seconds.
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)
                
            for query in connection.queries:
                query_time = query.get('time')
                if query_time is None:
                    query_time = query.get('duration', 0) / 1000
                
                if float(query_time) < 0.5:continue
                logger.debug('query: %s' % (query))
                
            logger.debug('%s queries run, total %s seconds' % (len(connection.queries), total_time))
        return response
    
# Orignal version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team

import sys
import os
import re
import hotshot, hotshot.stats
import tempfile
import StringIO

from django.conf import settings


words_re = re.compile( r'\s+' )

group_prefix_re = [
    re.compile( "^.*/django/[^/]+" ),
    re.compile( "^(.*)/[^/]+$" ), # extract module path
    re.compile( ".*" ),           # catch strange entries
]

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode, is available for superuser otherwise,
    but you really shouldn't add this middleware to any production configuration.

    WARNING: It uses hotshot profiler which is not thread safe.
    """
    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and ('prof' in request.GET or getattr(settings, 'PROFILING', False)):
            path = getattr(settings, 'PROFILE_DIR', './profiling')
            if not os.path.exists(path):
                os.makedirs(path)
                os.chmod(path, 0755)
            profname = "%s.prof" % (request.path.strip("/").replace('/', '.'))
            profname = os.path.join(path, profname)
            self.tmpfile = profname
            self.prof = hotshot.Profile(self.tmpfile)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and ('prof' in request.GET or getattr(settings, 'PROFILING', False)):
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def get_group(self, file):
        for g in group_prefix_re:
            name = g.findall( file )
            if name:
                return name[0]

    def get_summary(self, results_dict, sum):
        list = [ (item[1], item[0]) for item in results_dict.items() ]
        list.sort( reverse = True )
        list = list[:40]

        res = "      tottime\n"
        for item in list:
            res += "%4.1f%% %7.3f %s\n" % ( 100*item[0]/sum if sum else 0, item[0], item[1] )

        return res

    def summary_for_files(self, stats_str):
        stats_str = stats_str.split("\n")[5:]

        mystats = {}
        mygroups = {}

        sum = 0

        for s in stats_str:
            fields = words_re.split(s);
            if len(fields) == 7:
                time = float(fields[2])
                sum += time
                file = fields[6].split(":")[0]

                if not file in mystats:
                    mystats[file] = 0
                mystats[file] += time

                group = self.get_group(file)
                if not group in mygroups:
                    mygroups[ group ] = 0
                mygroups[ group ] += time

        return "<pre>" + \
               " ---- By file ----\n\n" + self.get_summary(mystats,sum) + "\n" + \
               " ---- By group ---\n\n" + self.get_summary(mygroups,sum) + \
               "</pre>"

    def process_response(self, request, response):
        if (settings.DEBUG or (request.user and request.user.is_superuser)) \
            and ('prof' in request.GET or getattr(settings, 'PROFILING', False)):
            self.prof.close()
            
            if 'prof' in request.GET:
                out = StringIO.StringIO()
                old_stdout = sys.stdout
                sys.stdout = out

                stats = hotshot.stats.load(self.tmpfile)
                stats.sort_stats('time', 'calls')
                stats.print_stats()

                sys.stdout = old_stdout
                stats_str = out.getvalue()

                if response and response.content and stats_str:
                    response.content = "<pre>" + stats_str + "</pre>"

                response.content = "\n".join(response.content.split("\n")[:40])

                response.content += self.summary_for_files(stats_str)

        return response


class AttachContentTypeMiddleware(object):
    def process_request(self, request):
        content_type = request.META.get('CONTENT_TYPE', '')
        if request.method == 'POST' and request.path.startswith('/rest/') and (not content_type or content_type.startswith('application/json')):
            request.META['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
            logger.warning('content_type invalid:%s ,%s'%(request.path, content_type))
