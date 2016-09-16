from django.dispatch import Signal

user_logged_in = Signal(providing_args=["obj"])

def testA(sender, obj, *args, **kwargs):
    print 'testA'
    # raise Exception('error a')

def testB(sender, obj, *args, **kwargs):
    print 'testB'
    # raise Exception('error b')

user_logged_in.connect(testA, dispatch_uid='testa')
user_logged_in.connect(testB, dispatch_uid='testb')

