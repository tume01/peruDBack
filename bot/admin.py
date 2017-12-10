# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Incident, IncidentType, PoliceStation


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'sender_id',
    )

@admin.register(IncidentType)
class IncidentTypeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
    )

@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'address',
    )