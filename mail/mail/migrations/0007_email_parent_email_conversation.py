# Generated by Django 5.1 on 2024-11-25 22:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0006_email_bcc_remove_email_cc_email_cc'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='parent_email',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replies', to='mail.email'),
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.ManyToManyField(related_name='replied_email', to='mail.email')),
            ],
        ),
    ]
