# -*- coding: utf-8 -*-
from model_utils.models import TimeStampedModel
from django.conf import settings
from django_mysql.models import Model
from django.db import models


class Category(TimeStampedModel, Model):

    name = models.CharField(
        max_length=5000,
        help_text='category name',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-created']
        default_permissions = settings.API_PERMISSIONS
