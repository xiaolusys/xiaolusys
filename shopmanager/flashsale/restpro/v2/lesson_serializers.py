# coding=utf-8
from rest_framework import serializers

from flashsale.xiaolumm.models_lesson import (
    LessonTopic,
    Instructor,
    Lesson,
    AttendRecord,
)


class LessonTopicSerializer(serializers.ModelSerializer):
    lesson_type_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = LessonTopic

class LessonSerializer(serializers.ModelSerializer):
    start_time_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    is_started = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Lesson

class InstructorSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Instructor

class AttendRecordSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = AttendRecord

        



