from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default settings for Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project3.settings')

# Initialize Celery
app = Celery('mail')

app.conf.enable_utc = False
app.conf.update(timezone='Asia/Karachi')

# Use settings from Django's settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
