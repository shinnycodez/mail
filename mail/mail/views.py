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


from .models import User, Email


def index(request):

    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, "mail/inbox.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def compose(request):

    # Composing a new email must be via POST
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    

    # Check recipient emails
    data = json.loads(request.body)
    print(data.get("recipients"))
    emails = [email.strip() for email in data.get("recipients").split(",")]
    if emails == [""]:
        return JsonResponse({
            "error": "At least one recipient required."
        }, status=400)

    # Convert email addresses to users
    recipients = []
    for email in emails:
        try:
            user = User.objects.get(email=email)
            recipients.append(user)
        except User.DoesNotExist:
            return JsonResponse({
                "error": f"User with email {email} does not exist."
            }, status=400)

    cc_emails = [cc_email.strip() for cc_email in data.get("cc").split(",")]
    cc_recipients = []
    if cc_emails != [""]:
        for cc_email in cc_emails:
            try:
                user = User.objects.get(email=cc_email)
                cc_recipients.append(user)
            except User.DoesNotExist:
                return JsonResponse({
                    "error": f"User with email {cc_email} does not exist."
                }, status=400)
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
                return JsonResponse({
                    "error": f"User with email {bcc_email} does not exist."
                }, status=400)
    else:
        pass


    # Get contents of email
    subject = data.get("subject", "")
    body = data.get("body", "")
    file = data.get("file", "")



    # Create one email for each recipient, plus sender
    users = set()
    users.add(request.user)
    users.update(recipients)
    if len(cc_recipients) > 0:
        users.update(cc_recipients)
    if len(bcc_recipients) > 0:
        users.update(bcc_recipients)
    for user in users:
        email = Email(
            user=user,
            sender=request.user,
            subject=subject,
            body=body,
            file=file,
            read=user == request.user,
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

    return JsonResponse({"message": "Email sent successfully."}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def mailbox(request, mailbox):
    
    # Filter emails returned based on mailbox
    print(request.user)
    if mailbox == "inbox":
        emails = Email.objects.filter(user=request.user,archived=False).filter( Q(recipients=request.user) |Q(cc=request.user) |Q(bcc=request.user) )

    elif mailbox == "sent":
        emails = Email.objects.filter(
            user=request.user, sender=request.user
        )
    elif mailbox == "archive":
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=True
        )
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    # Return emails in reverse chronologial order
    emails = emails.order_by("-timestamp").all()
    return JsonResponse([email.serialize() for email in emails], safe=False)


@csrf_exempt
@login_required
def email(request, email_id):

    # Query for requested email
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except Email.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    # Return email contents
    if request.method == "GET":
        return JsonResponse(email.serialize())

    # Update whether email is read or should be archived
    elif request.method == "PUT":
        data = json.loads(request.body)
        if data.get("read") is not None:
            email.read = data["read"]
        if data.get("archived") is not None:
            email.archived = data["archived"]
        email.save()
        return HttpResponse(status=204)

    # Email must be via GET or PUT
    else:
        return JsonResponse({
            "error": "GET or PUT request required."
        }, status=400)
    
@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = data.get("email", "")
    password = data.get("password", "")

    if not email:
        return JsonResponse({"error": "Email field is null"}, status=400)
    if not password:
        return JsonResponse({"error": "Password field is null"}, status=400)

    user = authenticate(request, username=email, password=password)
    request.user = user

    if user is not None:
        login(request, user)
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "pfp": user.pfp.url if user.pfp else None,
            }
        }, status=200)
    else:
        return JsonResponse({"error": "Failed to login"}, status=400)



def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Post method required"}, status=400)

    data = json.loads(request.body)
    email = data.get("email", "")
    password = data.get("password", "")
    

    if len(email) <= 0:
        return JsonResponse({"error": "email field is null"}, status=400)
    if len(password) <= 0:
        return JsonResponse({"error": "password field is null"}, status=400)

    try:
        auth_user = User.objects.get(email=email)
        if auth_user:
            return JsonResponse({"error": "Email already exists"}, status=400)
    except User.DoesNotExist:
        pass        

    username = email.split('@')[0]

    # Attempt to create new user
    try:
        user = User.objects.create_user(username, email, password)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        user.save()
    except IntegrityError as e:
        print(e)

        return JsonResponse({"error": "Failed to register"}, status=400)
    
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    request.user = user

    refresh = RefreshToken.for_user(user)
    return JsonResponse({
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "pfp": user.pfp.url if user.pfp else None,
        }
    }, status=200)





User = get_user_model()

class GoogleLoginCallbackView(APIView):
    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token missing'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify the token with Google
        google_verify_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(google_verify_url, headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        
        # Extract user info
        email = user_info.get('email')
        name = user_info.get('name')
        pfp = user_info.get('picture')
        
        
        if not email:
            return Response({'error': 'Email not provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists or create a new one
        user, created = User.objects.get_or_create(email=email, defaults={'username': name})
        user.pfp = pfp
        user.save()

        request.user = user
        print(user)
        print(request.user)


        # Generate a JWT token for the user
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'pfp': user.pfp,
            }
        }, status=status.HTTP_200_OK)