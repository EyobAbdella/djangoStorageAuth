from django.conf import settings
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField


class OAuthTokens(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oauth_tokens"
    )
    google_access = EncryptedCharField(max_length=255)
    google_refresh = EncryptedCharField(max_length=255)
    microsoft_access = EncryptedCharField(max_length=255)
    microsoft_refresh = EncryptedCharField(max_length=255)
    microsoft_expiry = models.DateTimeField(auto_now_add=True)
