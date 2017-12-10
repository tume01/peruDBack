# -*- coding: utf-8 -*-
from bot.models import Incident
from rest_framework import serializers


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'
