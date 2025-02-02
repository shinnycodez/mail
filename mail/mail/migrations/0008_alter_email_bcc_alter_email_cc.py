# Generated by Django 5.1 on 2024-11-26 20:43

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0007_email_parent_email_conversation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='bcc',
            field=models.ManyToManyField(null=True, related_name='emails_received_bcc', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='email',
            name='cc',
            field=models.ManyToManyField(null=True, related_name='emails_received_cc', to=settings.AUTH_USER_MODEL),
        ),
    ]
