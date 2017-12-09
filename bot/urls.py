# -*- coding: utf-8 -*-
from bot.views import MessageViewSet
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'messages', MessageViewSet)
urlpatterns = router.urls
