
from random import SystemRandom
from urllib.parse import urlencode
import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.cache import cache
from django.shortcuts import redirect
from oauthlib.common import UNICODE_ASCII_CHARACTER_SET
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OAuthTokens
from .serializers import UserSerializer

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


        user, _ = User.objects.get_or_create(email=email)
        login(request, user)

        oauth_tokens, _ = OAuthTokens.objects.get_or_create(user=user)
        oauth_tokens.google_access = access_token
        oauth_tokens.google_refresh = refresh_token 

        user.save()

        refresh = RefreshToken.for_user(user)
        token = TokenObtainPairSerializer().get_token(user)

        return Response({
            "access_token": str(token.access_token),
            "refresh_token": str(refresh),
        }, status=status.HTTP_200_OK)

