# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


public_apis = [
    url(r'^api/v1/', include([
        url(r'', include('bot.urls')),
        url(r'', include('category.urls')),
    ])),
]

urlpatterns = [
    url(r'^', include(public_apis, namespace='public_apis')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
