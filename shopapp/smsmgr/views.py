# -*- coding:utf8 -*-
import re
import datetime
import json
from django.http import HttpResponse, HttpResponseNotFound
import logging

logger = logging.getLogger('smsmgr.handler')
