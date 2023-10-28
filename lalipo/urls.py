"""
URL configuration for lalipo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("", views.input_playlist_view, name="input_playlist"),
    path("generate/", views.generate_playlist_view, name="generate_playlist"),
    path("preview/", views.preview_playlist_view, name="preview_playlist"),
    path("preview_test/", views.preview_playlist_test_view, name="preview_playlist_test"),
    path("create/", views.create_playlist_view, name="create_playlist"),
]
