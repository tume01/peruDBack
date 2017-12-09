# -*- coding: utf-8 -*-
from category.views import CategoryViewSet
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'categories', CategoryViewSet)
urlpatterns = router.urls
