from django.contrib.auth.models import AbstractUser
from django.db import models
import json


class User(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    pfp = models.TextField(max_length=10000, blank=True, null=True)
    def __str__(self):
        return self.email


class Email(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="emails")
    sender = models.ForeignKey("User", on_delete=models.PROTECT, related_name="emails_sent")
    recipients = models.ManyToManyField("User", related_name="emails_received")
    subject = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.TextField(blank=True, null=True)
    read = models.BooleanField(default=False)
    cc = models.ManyToManyField("User", related_name="emails_received_cc")
    bcc = models.ManyToManyField("User", related_name="emails_received_bcc")
    archived = models.BooleanField(default=False)

    def serialize(self):
        

        return {
            "id": self.id,
            "sender": self.sender.email,
            "pfp": self.sender.pfp,
            "recipients": [user.email for user in self.recipients.all()],
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
            "file": self.file,
            "cc": [user.email for user in self.cc.all()],
            "bcc": [user.email for user in self.bcc.all()],
            "read": self.read,
            "archived": self.archived
        }
