"""
URL configuration for shareaichat project.

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
from base.forms import AuthAdminForm
from django.conf.urls import handler400, handler403, handler404, handler500
from base import views as base_views

admin.site.login_form = AuthAdminForm
admin.site.login_template = 'registration/login.html'

urlpatterns = [
    path("obscure/", admin.site.urls),
    path("", include("base.urls")),
    path("", include("main.urls")),
]

handler400 = base_views.handler400
handler403 = base_views.handler403
handler404 = base_views.handler404
handler500 = base_views.handler500