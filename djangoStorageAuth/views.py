from datetime import datetime, timedelta
from random import SystemRandom
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.cache import cache
from django.shortcuts import redirect
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from oauthlib.common import UNICODE_ASCII_CHARACTER_SET
from .models import OAuthTokens
from .serializers import UserSerializer
import requests
import jwt


User = get_user_model()


class GoogleRedirectViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        SCOPES = [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "openid",
        ]

        rand = SystemRandom()
        state = "".join(rand.choice(UNICODE_ASCII_CHARACTER_SET) for _ in range(30))
        cache.set(state, True, timeout=500)

        redirect_uri = request.build_absolute_uri("/oauth/google/callback")

        params = {
            "response_type": "code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": " ".join(SCOPES),
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
        }

        authorization_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
        return redirect(authorization_url) 

class GoogleCallbackViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if not code or not state:
            return Response({"error": "code and state are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not cache.get(state):
            return Response({"error": "Invalid or expired state."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(state)

        token_endpoint = "https://oauth2.googleapis.com/token"
        redirect_uri = request.build_absolute_uri("/oauth/google/callback")
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        token_response = requests.post(token_endpoint, data=data)
        if not token_response.ok:
            return Response({"error": "Failed to exchange code for token"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = token_response.json()
        id_token = tokens.get("id_token")

        if not id_token:
            return Response({"error": "Missing ID token"}, status=status.HTTP_400_BAD_REQUEST)

        decoded = jwt.decode(id_token, options={"verify_signature": False})
        email = decoded.get("email")
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")


        user, _ = User.objects.get_or_create(email=email, username=email)
        login(request, user)

        oauth_tokens, _ = OAuthTokens.objects.get_or_create(user=user)
        oauth_tokens.google_access = access_token
        oauth_tokens.google_refresh = refresh_token 
        oauth_tokens.save()
        refresh = RefreshToken.for_user(user)
        token = TokenObtainPairSerializer().get_token(user)

        return Response({
            "access_token": str(token.access_token),
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)






class MicrosoftRedirectViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        SCOPES = [
            "User.Read",
            "Files.ReadWrite",
        ]

        rand = SystemRandom()
        state = "".join(rand.choice(UNICODE_ASCII_CHARACTER_SET) for _ in range(30))
        cache.set(state, True, timeout=500)

        redirect_uri = request.build_absolute_uri("/oauth/microsoft/callback/")
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(SCOPES),
            "state": state,
            "response_mode": "query",
        }

        authorization_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"
        return redirect(authorization_url)

class MicrosoftCallbackViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        if not code or not state:
            return Response({"error": "code and state are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not cache.get(state):
            return Response({"error": "Invalid or expired state."}, status=status.HTTP_400_BAD_REQUEST)

        cache.delete(state)

        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        redirect_uri = request.build_absolute_uri("/oauth/microsoft/callback/")
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        data = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        response = requests.post(token_url, data=data)
        if not response.ok:
           return Response({"error": "Failed to exchange code for token"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        expires_in = tokens.get("expires_in")
        expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)


        if not access_token:
            return Response({"error": "Access token missing"}, status=status.HTTP_400_BAD_REQUEST)

        user_info_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)

        if not user_info_response.ok:
            return Response({"error": "Failed to fetch user info from Microsoft"}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_info_response.json()
        email = user_info.get("userPrincipalName")

        if not email:
            return Response({"error": "Email not found in Microsoft user info"}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(email=email, username=email)
        login(request, user)
        oauth_tokens, _ = OAuthTokens.objects.get_or_create(user=user)
        oauth_tokens.microsoft_access = access_token
        oauth_tokens.microsoft_refresh = refresh_token 
        oauth_tokens.microsoft_expiry = expiration_time 
        oauth_tokens.save()


        refresh = RefreshToken.for_user(user)
        token = TokenObtainPairSerializer().get_token(user)

        return Response({
            "access_token": str(token.access_token),
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)


