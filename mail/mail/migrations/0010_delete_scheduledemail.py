# Generated by Django 5.1 on 2024-11-30 18:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0009_scheduledemail_delete_conversation'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ScheduledEmail',
        ),
    ]