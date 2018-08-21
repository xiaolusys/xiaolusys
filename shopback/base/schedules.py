from datetime import datetime
from celery.schedules import crontab, schedule


class first_of_month(schedule):
    def is_due(self, last_run_at):
        now = datetime.now()
        if now.month > last_run_at.month and now.day == 1:
            return True, 60
        return False, 60

    def __repr__(self):
        return "<first of month>"
