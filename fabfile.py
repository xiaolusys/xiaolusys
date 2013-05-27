from time import sleep
from fabric.api import env, run, local, cd, puts, settings
from fabric.contrib.files import exists

REPO_DIR="/home/user1/repo/"
DEPLOY_DIR="/home/user1/deploy/"

def staging():
    """docstring for production"""
    env.hosts = ['user1@173.164.135.13'] # replace with real setting
    env.base_dir = '/home/user1/deploy/taobao'
    env.repo_url = 'file:///home/user1/repo/taobao-backend.git'
    env.require_file = 'requirements_staging.txt'
    env.setup_file   = 'stage_settings.py'

def ny():
    """docstring for ny"""
    env.hosts = ['user1@ny'] # replace with real setting
    env.base_dir = '/home/user1/deploy/taobao'
    env.repo_url = 'file:///home/user1/repo/taobao-backend.git'
    env.require_file = 'requirements.txt'
    env.setup_file   = 'ny_settings.py'

def s1():
    """docstring for production"""
    env.hosts = ['user1@s1'] # replace with real setting
    env.base_dir = '/home/user1/deploy/taobao'
    env.repo_url = 'file:///home/user1/repo/taobao-backend.git'
    env.require_file = 'requirements_production.txt'
    env.setup_file   = 's1_settings.py'
    
def production():
    """docstring for production"""
    env.hosts = ['user1@222.73.86.185'] # replace with real setting
    env.base_dir = '/home/user1/deploy/taobao'
    env.repo_url = 'file:///home/user1/repo/taobao-backend.git'
    env.require_file = 'requirements_production.txt'
    env.setup_file   = 'prod_settings.py'

def get_version():
    """docstring for get_version"""
    version = local('git describe --tags', True)
    env.version = version
    env.version_dir = '%s/taobao-%s' % (env.base_dir, env.version) 

def init_code_base():
    """docstring for init_code_base"""
    with cd(env.base_dir):
        run('git clone %s taobao-%s' % (env.repo_url, env.version))

def init_virtualenv():
    """docstring for init_virtualenv"""
    with cd(env.version_dir):
        run('virtualenv --system-site-packages ve')
        run('source ve/bin/activate;pip install -r %s' % env.require_file)

def get_static():
    """docstring for get_static"""
    pass
    #with cd(env.version_dir):
        #run('git clone file:///home/user1/repo/renpin-frontend.git static')
        #run('git submodule init')
        #run('git submodule update')

def set_local_settings():
    """docstring for set_local_settings"""
    with cd(env.version_dir):
        run('cp ./%s shopmanager/local_settings.py'%env.setup_file)

def collect_static():
    """docstring for collect_static"""
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py collectstatic --noinput')
        run('cd ../site_media;unlink static;ln -s %s/shopmanager/site_media/static static' % env.version_dir)

def collect_download():
    """docstring for collect_static"""
    with cd(env.version_dir):
        run('cd %s/shopmanager/site_media;rm -rf download;ln -s ../../../site_media/download' % env.version_dir)
        
def collect_asyncfile():
    """docstring for collect_static"""
    with cd(env.version_dir):
        run('cd %s/shopmanager/site_media;rm -rf asyncfile;ln -s ../../../site_media/asyncfile' % env.version_dir)
        
def collect_closure_library():
    """docstring for collect_static"""
    with cd(env.version_dir):
        run('cd %s/shopmanager/site_media/static;unlink closure-library;ln -s /home/user1/deploy/google-closure/closure-library' % env.version_dir)

def deploy():
    """docstring for deploy"""
    get_version()
    if not exists(env.version_dir):
        init_code_base()
        init_virtualenv()
        #get_static() # this is a hack for buggy network and should be removed in the future
        set_local_settings()
        collect_static()
        collect_download()
        collect_asyncfile()
        collect_closure_library()

def restart_gunicorn():
    """docstring for restart_gunicorn"""
    if exists('/home/user1/deploy/taobao/gunicorn.pid'):
        run('kill -QUIT `cat /home/user1/deploy/taobao/gunicorn.pid`')
        with settings(warn_only=True):
            run("ps auxww | grep taobao_gunicorn_conf | awk '{ print $2 }' |xargs kill -KILL")
        run('rm -rf /home/user1/deploy/taobao/gunicorn.pid')
    get_version()
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py run_gunicorn --config=taobao_gunicorn_conf.py ')


def restart_celeryd():
    if exists('/home/user1/deploy/taobao/celery.pid'):
        run('kill -QUIT `cat /home/user1/deploy/taobao/celery.pid`')
        puts('Sleep 30 seconds before celery fully shutdown')
        sleep(30)
        with settings(warn_only=True):
            run("ps auxww | grep taobao/celery.err | awk '{ print $2 }' |xargs kill -KILL")
        run('rm -rf /home/user1/deploy/taobao/celery.pid')
    get_version()
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py celerydaemon --pidfile=/home/user1/deploy/taobao/celery.pid --stdout=/home/user1/deploy/taobao/celery.out --stderr=/home/user1/deploy/taobao/celery.err')

def restart_notifyserver():
    if exists('/home/user1/deploy/taobao/notify.pid'):
        run('kill -QUIT `cat /home/user1/deploy/taobao/notify.pid`')
        puts('Sleep 30 seconds before notify receiver fully shutdown')
        sleep(30)
        with settings(warn_only=True):
            run("ps auxww | grep taobao/notify.err | awk '{ print $2 }' |xargs kill -KILL")
        run('rm -rf /home/user1/deploy/taobao/notify.pid')
    get_version()
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py topnotifyreceiver --pidfile=/home/user1/deploy/taobao/notify.pid --stdout=/home/user1/deploy/taobao/notify.out --stderr=/home/user1/deploy/taobao/notify.err')


def restart_celerybeat():
    if exists('/home/user1/deploy/taobao/celerybeat.pid'):
        run('kill -QUIT `cat /home/user1/deploy/taobao/celerybeat.pid`')
        puts('Sleep 10 seconds before celery fully shutdown')
        sleep(10)
        with settings(warn_only=True):
            run("ps auxww | grep taobao/celerybeat.err | awk '{ print $2 }' |xargs kill -KILL")
        run('rm -rf /home/user1/deploy/taobao/celerybeat.pid')
    get_version()
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py celery_beat --working_directory=/home/user1/deploy/taobao/ --stdout=/home/user1/deploy/taobao/celerybeat.out --stderr=/home/user1/deploy/taobao/celerybeat.err')


def restart_celerycam():
    if exists('/home/user1/deploy/taobao/celeryev.pid'):
        run('kill -QUIT `cat /home/user1/deploy/taobao/celeryev.pid`')
        puts('Sleep 10 seconds before celeryev fully shutdown')
        sleep(10)
        with settings(warn_only=True):
            run("ps auxww | grep taobao/celeryev.err | awk '{ print $2 }' |xargs kill -KILL")
        run('rm -rf /home/user1/deploy/taobao/celeryev.pid')
    get_version()
    with cd(env.version_dir):
        run('source ve/bin/activate;cd shopmanager;python manage.py celery_cam  --working_directory=/home/user1/deploy/taobao/ --stdout=/home/user1/deploy/taobao/celeryev.out --stderr=/home/user1/deploy/taobao/celeryev.err')


def restart():
    """docstring for restart"""
    restart_gunicorn()
    restart_celeryd()
    restart_celerybeat()
    #restart_celerycam() #use for nondb backend,like rabbitmq,redis .etc.
  
