#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    from global_setup import setup_djagno_environ
    setup_djagno_environ()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
