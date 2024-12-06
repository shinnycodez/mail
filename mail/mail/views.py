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

from .utils import compose, SaveScheduledEmail
from .models import User, Email, ScheduledEmail

  

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def EmailComposeView(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    data = json.loads(request.body)

    if data.get("scheduled_time"):
        msg = SaveScheduledEmail(data, request.user)
        return JsonResponse(msg)
    
    msg = compose(data, request.user)
    print(msg)
    return JsonResponse(msg,status=msg.get("status"))






@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def mailbox(request, mailbox):
    
    # Filter emails returned based on mailbox
    print(request.user)
    if mailbox == "inbox":
        emails = Email.objects.filter(user=request.user,archived=False, parent_email__isnull=True).filter( Q(recipients=request.user) |Q(cc=request.user) |Q(bcc=request.user) )

    elif mailbox == "sent":
        emails = Email.objects.filter(
            user=request.user, sender=request.user, parent_email__isnull=True
        )
    elif mailbox == "archive":
        emails = Email.objects.filter(
            user=request.user, recipients=request.user, archived=True, parent_email__isnull=True
        )
    elif mailbox == "schedule":
        emails = ScheduledEmail.objects.filter(sender=request.user)
        emails.order_by("-scheduled_time").all()
        return JsonResponse([email.serialize() for email in emails], safe=False)
    else:
        return JsonResponse({"error": "Invalid mailbox."}, status=400)

    # Return emails in reverse chronologial order
    emails = emails.order_by("-timestamp").all()
    return JsonResponse([email.serialize() for email in emails], safe=False)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def email(request, email_id):

    
    try:
        email = Email.objects.get(user=request.user, pk=email_id)
    except Email.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    
    if request.method == "GET":
        email = email.serialize()
        
        return JsonResponse({"email": email}, safe=False)

    
    elif request.method == "PUT":
    
        data = json.loads(request.body)
        if data.get("read") is not None:
            email.read = data["read"]

        if data.get("archived") is not None:
            email.archived = data["archived"]
        email.save()
        return HttpResponse(status=204)
    
    elif request.method == 'DELETE' : 
        email.delete()
        return JsonResponse({
            "success" : "Deleted successfully"
        })
    
    
    else:
        return JsonResponse({
            "error": "GET or PUT or DELETE request required."
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def logout_view(request):
    logout(request)
    return JsonResponse({"success" : "successfully logged out"})

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
    



@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
@login_required
def Scheduled_email(request, email_id):

    
    try:
        email = ScheduledEmail.objects.get(sender=request.user, pk=email_id)
    except ScheduledEmail.DoesNotExist:
        return JsonResponse({"error": "Email not found."}, status=404)

    print(email)
    if request.method == "GET":
        email = email.serialize()
        
        return JsonResponse({"email": email}, safe=False)

    
    elif request.method == 'DELETE' : 
        email.delete()
        return JsonResponse({
            "success" : "Deleted successfully"
        })
    
  
    else:
        return JsonResponse({
            "error": "GET or PUT or DELETE request required."
        }, status=400)