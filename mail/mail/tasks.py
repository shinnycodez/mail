from celery import shared_task
from django.utils.timezone import now
from .models import ScheduledEmail, User
from django.http import JsonResponse
from .utils import compose, scheduled_compose

@shared_task(bind=True)
def send_scheduled_emails(*args, **kwargs):
    email_queryset = ScheduledEmail.objects.filter(scheduled_time__lte=now()).prefetch_related('recipients')
    
    emails = [
        {
            **email,
            "recipients": list(ScheduledEmail.objects.get(id=email["id"]).recipients.values('id')),
            "cc": list(ScheduledEmail.objects.get(id=email["id"]).cc.values('id')),
            "bcc": list(ScheduledEmail.objects.get(id=email["id"]).bcc.values('id')),
        }
        for email in email_queryset.values()  # Add all required fields here
    ]

    print(emails)  # This will include recipients as a list of dictionaries
    if emails:
        for email in emails:
            # Send email logic
            user = User.objects.get(id=email["sender_id"])
            msg = scheduled_compose(email, user)
            ScheduledEmail.objects.filter(id=email["id"]).delete()  # Ensure deletion by ID
        return msg
    else:
        msg = "No scheduled emails yet!"
        return msg

        
