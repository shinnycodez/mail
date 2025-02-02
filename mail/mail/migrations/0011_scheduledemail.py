# Generated by Django 5.1 on 2024-11-30 18:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0010_delete_scheduledemail'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField(blank=True)),
                ('file', models.TextField(blank=True, null=True)),
                ('read', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False)),
                ('scheduled_time', models.DateTimeField()),
                ('bcc', models.ManyToManyField(null=True, related_name='emails_to_be_sent_to_bcc', to=settings.AUTH_USER_MODEL)),
                ('cc', models.ManyToManyField(null=True, related_name='emails_to_be_sent_to_cc', to=settings.AUTH_USER_MODEL)),
                ('recipients', models.ManyToManyField(related_name='emails_to_be_sent_to', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_emails_sent', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_emails', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
