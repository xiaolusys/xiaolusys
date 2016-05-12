# coding=utf-8
from rest_framework import serializers

from flashsale.xiaolumm.models_lesson import (
    LessonTopic,
    Instructor,
    Lesson,
    LessonAttendRecord,
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
    m_static_url = serializers.CharField(read_only=True)
    
    class Meta:
        extra_kwargs = {'customer_idx': {'read_only': True}}
        model = Lesson
        fields = ('id', 'lesson_topic_id', 'title', 'description', 'content_link', 'instructor_id',
                  'instructor_name', 'instructor_title', 'instructor_image', 'num_attender',
                  'num_score', 'start_time_display', 'qrcode_links', 'status', 'status_display',
                  'is_started', 'customer_idx', 'm_static_url')

class InstructorSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    apply_date = serializers.CharField(read_only=True)
    
    class Meta:
        model = Instructor

class LessonAttendRecordSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(read_only=True)
    signup_time = serializers.CharField(read_only=True)
    signup_date = serializers.CharField(read_only=True)
    class Meta:
        model = LessonAttendRecord

        



