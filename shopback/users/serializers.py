# coding=utf-8
from rest_framework import serializers
from django.contrib.auth.models import User, Group


class GroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class UserSimpleSerializer(serializers.ModelSerializer):
    user_groups = GroupSimpleSerializer(source='groups', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'user_groups', 'is_staff')