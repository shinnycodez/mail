import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import HttpResponse, HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.utils import timezone
from pytz import timezone as pytz_timezone



from .models import User, Email, ScheduledEmail



def scheduled_compose(data, request_user):


    print(data)
    recipient_ids = [recipient['id'] for recipient in data['recipients']]
    recipients = []
    for recipient in recipient_ids:
        try:
            user = User.objects.get(id=recipient)
            recipients.append(user)
        except User.DoesNotExist:
            return {"error": "Receipent does not exists!", "status" : 400}
        
    cc_ids = [recipient['id'] for recipient in data['cc']]
    cc_recipients = []
    if cc_ids != [""]:
        for cc_email in cc_ids:
            try:
                user = User.objects.get(id=cc_email)
                cc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {cc_email} does not exist.", "status" : 400,
                }
    else:
        pass

    bcc_ids = [recipient['id'] for recipient in data['bcc']]
    
    bcc_recipients = []
    if bcc_ids != [""]:
        for bcc_email in bcc_ids:
            try:
                user = User.objects.get(id=bcc_email)
                bcc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {bcc_email} does not exist.", "status" : 400,
                }
    else:
        pass


    # Get contents of email
    subject = data["subject"]
    body = data["body"]
    file = data["file"]
    tz = pytz_timezone('Asia/Karachi')
    timezone.activate(tz)

    # Example: Get the current time in the selected timezone
    timestamp = timezone.localtime(timezone.now())

    


    # Create one email for each recipient, plus sender
    users = set()
    users.add(request_user)
    users.update(recipients)
    if len(cc_recipients) > 0:
        users.update(cc_recipients)
    if len(bcc_recipients) > 0:
        users.update(bcc_recipients)
    for user in users:
        email = Email(
            user=user,
            sender=request_user,
            subject=subject,
            body=body,
            file=file,
            read=user == request_user,
            timestamp=timestamp,
        )
        email.save()
        for recipient in recipients:
            email.recipients.add(recipient)
        email.save()
        if len(cc_recipients) > 0:
            for cc_recipient in cc_recipients:
                email.cc.add(cc_recipient)
            email.save()
        if len(bcc_recipients) > 0:
            for bcc_recipient in bcc_recipients:
                email.bcc.add(bcc_recipient)
            email.save()

    return {"message": "Email sent successfully."}




def SaveScheduledEmail(data, request_user):
    emails = [email.strip() for email in data.get("recipients").split(",")]
    if emails == [""]:
        return {
            "error": "At least one recipient required." , "status" : 400,
        }

    # Convert email addresses to users
    recipients = []
    for email in emails:
        try:
            user = User.objects.get(email=email)
            recipients.append(user)
        except User.DoesNotExist:
            return {
                "error": f"User with email {email} does not exist." , "status" : 400,
            }

    cc_emails = [cc_email.strip() for cc_email in data.get("cc").split(",")]
    cc_recipients = []
    if cc_emails != [""]:
        for cc_email in cc_emails:
            try:
                user = User.objects.get(email=cc_email)
                cc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {cc_email} does not exist.", "status" : 400,
                }
    else:
        pass

    bcc_emails = [bcc_email.strip() for bcc_email in data.get("bcc").split(",")]
    
    bcc_recipients = []
    if bcc_emails != [""]:
        for bcc_email in bcc_emails:
            try:
                user = User.objects.get(email=bcc_email)
                bcc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {bcc_email} does not exist.", "status" : 400,
                }
    else:
        pass


    # Get contents of email
    subject = data.get("subject", "")
    body = data.get("body", "")
    file = data.get("file", "")
    scheduled_time = data.get("scheduled_time", "")
    if scheduled_time is "":
        return {"error": "Scheduled time not provided", "status" : 400,}
    

    


    # Create one email for each recipient, plus sender
    users = set()
    users.add(request_user)
    users.update(recipients)
    if len(cc_recipients) > 0:
        users.update(cc_recipients)
    if len(bcc_recipients) > 0:
        users.update(bcc_recipients)
    
    email = ScheduledEmail(
        sender=request_user,
        subject=subject,
        body=body,
        file=file,
        read=user == request_user,
        scheduled_time = scheduled_time,
    )
    email.save()
    for recipient in recipients:
        email.recipients.add(recipient)
    email.save()
    if len(cc_recipients) > 0:
        for cc_recipient in cc_recipients:
            email.cc.add(cc_recipient)
        email.save()
    if len(bcc_recipients) > 0:
        for bcc_recipient in bcc_recipients:
            email.bcc.add(bcc_recipient)
        email.save()

    return {"message": "Email saved successfully."}



def compose(data, request_user):


    emails = [email.strip() for email in data.get("recipients").split(",")]
    if emails == [""]:
        return {
            "error": "At least one recipient required.","status" : 400
        }

    # Convert email addresses to users
    recipients = []
    for email in emails:
        try:
            user = User.objects.get(email=email)
            recipients.append(user)
        except User.DoesNotExist:
            return {
                "error": f"User with email {email} does not exist.", "status" : 400,
            }

    cc_emails = [cc_email.strip() for cc_email in data.get("cc").split(",")]
    cc_recipients = []
    if cc_emails != [""]:
        for cc_email in cc_emails:
            try:
                user = User.objects.get(email=cc_email)
                cc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {cc_email} does not exist.", "status" : 400,
                }
    else:
        pass

    bcc_emails = [bcc_email.strip() for bcc_email in data.get("bcc").split(",")]
    
    bcc_recipients = []
    if bcc_emails != [""]:
        for bcc_email in bcc_emails:
            try:
                user = User.objects.get(email=bcc_email)
                bcc_recipients.append(user)
            except User.DoesNotExist:
                return {
                    "error": f"User with email {bcc_email} does not exist.", "status" : 400,
                }
    else:
        pass


    # Get contents of email
    subject = data.get("subject", "")
    body = data.get("body", "")
    file = data.get("file", "")
    tz = pytz_timezone('Asia/Karachi')
    timezone.activate(tz)

    # Example: Get the current time in the selected timezone
    timestamp = timezone.localtime(timezone.now())
    print(timestamp)


    # Create one email for each recipient, plus sender
    users = set()
    users.add(request_user)
    users.update(recipients)
    if len(cc_recipients) > 0:
        users.update(cc_recipients)
    if len(bcc_recipients) > 0:
        users.update(bcc_recipients)
    for user in users:
        email = Email(
            user=user,
            sender=request_user,
            subject=subject,
            body=body,
            file=file,
            read=user == request_user,
            timestamp=timestamp,
        )
        email.save()
        for recipient in recipients:
            email.recipients.add(recipient)
        email.save()
        if len(cc_recipients) > 0:
            for cc_recipient in cc_recipients:
                email.cc.add(cc_recipient)
            email.save()
        if len(bcc_recipients) > 0:
            for bcc_recipient in bcc_recipients:
                email.bcc.add(bcc_recipient)
            email.save()

    return {"message": "Email sent successfully."}