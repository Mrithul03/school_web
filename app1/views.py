from django.shortcuts import render, redirect
from django.views import View

from .models import UserProfile,School
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
import requests
from django.contrib import messages

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    school_code = request.data.get('school_code')
    phone =  request.data.get('phone')
    password = request.data.get('password')
    # fcm_token = request.data.get('fcm_token')  # 👈 Get FCM token from frontend

    print(f"📥 Login attempt:school_code={school_code} phone={phone}, password={password}")

    try:
        profile = UserProfile.objects.get(phone=phone)
        user = profile.user

        # ✅ Check if school_code matches
        school = School.objects.get(school_code=school_code)

        # Now check if the user’s school matches this instance
        if profile.school != school:
            return Response({'error': 'User does not belong to this school'}, status=401)

        # ✅ Check password
        if not user.check_password(password):
            print("❌ Invalid password")
            return Response({'error': 'Invalid password'}, status=401)

        # ✅ Clear previous tokens
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        # if fcm_token:
        #     profile.fcm_token = fcm_token
        profile.save()

        return Response({
            'message': 'Login successful',
            'token': token.key,
            'user_id': user.id,
            'name': user.username,
            'phone': profile.phone,
            'role': profile.role,
        }, status=status.HTTP_200_OK)

    except UserProfile.DoesNotExist:
        print("❌ UserProfile not found")
        return Response({'error': 'User does not exist'}, status=404)
