# -*- coding: utf-8 -*-
from model_utils.models import TimeStampedModel
from django.conf import settings
from django_mysql.models import Model, JSONField
from django.db import models


class Message(TimeStampedModel, Model):

    text = models.CharField(
        max_length=5000,
        help_text='user message',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-created']
        default_permissions = settings.API_PERMISSIONS


class Conversation(TimeStampedModel):

    context = JSONField()
    sender_id = models.CharField(
        max_length=5000,
    )

    grade = models.CharField(
        max_length=100,
        null=True,
    )

    confidence_person = models.CharField(
        max_length=100,
        null=True,
    )

    grade_section = models.CharField(
        max_length=100,
        null=True,
    )

    grade_level = models.CharField(
        max_length=100,
        null=True,
    )

    problem_location = models.CharField(
        max_length=100,
        null=True,
    )

    genre = models.CharField(
        max_length=10,
        null=True,
    )

    violence_type = models.CharField(
        max_length=100,
        null=True,
    )

    topics = JSONField()

    district = models.CharField(
        max_length=100,
        null=True,
    )

    sentiment = models.CharField(
        max_length=100,
        null=True,
    )

    sentiment_value = models.DecimalField(
        max_digits=19,
        decimal_places=10,
        null=True,
    )

    detect_sentiment = models.NullBooleanField()

    class Meta:
        ordering = ['-created']
        default_permissions = settings.API_PERMISSIONS
