from django.urls import path

from . import views

urlpatterns = [
    path("google/redirect", views.GoogleRedirectViewSet.as_view({"get": "list"})),
    path("google/callback", views.GoogleCallbackViewSet.as_view({"get": "list"})),
]
