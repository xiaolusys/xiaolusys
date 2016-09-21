# encoding=utf8
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.settings")
from flashsale.pay.models.user import Customer


def main():
    print Customer.objects.all().using('product').count()


if __name__ == '__main__':
    main()
