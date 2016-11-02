from django.conf.urls import patterns, url

urlpatterns = patterns('shopapp.jingdong.views',

                       url(r'login/$', 'loginJD', name='login_jd'),
                       url(r'login/auth/$', 'loginAuthJD', name='login_auth_jd'),

                       )
