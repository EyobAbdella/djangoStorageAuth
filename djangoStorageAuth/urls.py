from django.urls import path

from . import views

urlpatterns = [
    path("google/redirect", views.GoogleRedirectViewSet.as_view({"get": "list"})),
    path("google/callback", views.GoogleCallbackViewSet.as_view({"get": "list"})),
    path("microsoft/redirect", views.MicrosoftRedirectViewSet.as_view({"get": "list"})),
    path("microsoft/callback/", views.MicrosoftCallbackViewSet.as_view({"get": "list"})),

]
