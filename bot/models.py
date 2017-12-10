# -*- coding: utf-8 -*-
from model_utils.models import TimeStampedModel
from django.conf import settings
from django_mysql.models import Model, JSONField
from django.db import models

class IncidentType(TimeStampedModel):

    INCIDENT = 1
    PRE_INCIDENT = 2
    name = models.CharField(
        max_length=50
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created']
        default_permissions = settings.API_PERMISSIONS

class Incident(TimeStampedModel):

    type = models.ForeignKey(
        IncidentType,
        on_delete=models.CASCADE,
        null=True,
    )

    sender_id = models.CharField(
        max_length=5000,
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
    )

    evidence_media = models.CharField(
        max_length=5000,
        blank=True,
        null=True,
    )

    is_anonymous = models.NullBooleanField()

    started = models.NullBooleanField()

    genre = models.CharField(
        max_length=50,
        null=True,
    )

    civil_state = models.CharField(
        max_length=50,
        null=True,
    )

    profession = models.CharField(
        max_length=50,
        null=True,
    )

    address = models.CharField(
        max_length=50,
        null=True,
    )

    age = models.IntegerField(
        null=True,
    )

    dni = models.CharField(
        max_length=50,
        null=True,
    )

    name = models.CharField(
        max_length=50,
        null=True,
    )

    date = models.DateField(null=True)

    time = models.TimeField(null=True)

    kind = models.CharField(
        max_length=50,
        null=True,
    )

    description = models.CharField(
        max_length=5000,
        null=True,
    )

    have_proof = models.NullBooleanField()

    requested_date = models.NullBooleanField()

    request_kind = models.NullBooleanField()

    proof_requested = models.NullBooleanField()

    evidence_requested = models.NullBooleanField()

    ended = models.NullBooleanField()

    location_requested = models.NullBooleanField()

    class Meta:
        ordering = ['-created']
        default_permissions = settings.API_PERMISSIONS
