# coding=utf-8
import random
from rest_framework import serializers

from flashsale.xiaolumm.models.models_lesson import (
    LessonTopic,
    Instructor,
    Lesson,
    LessonAttendRecord,
)


class LessonTopicSerializer(serializers.ModelSerializer):
    lesson_type_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    click_num_show = serializers.SerializerMethodField(method_name='random_click_num', read_only=True)

    class Meta:
        model = LessonTopic
        fields = (
            'id',
            'title',
            'cover_image',
            'description',
            'num_attender',
            'content_link',
            'lesson_type',
            'is_show',
            'status',
            'order_weight',
            'click_num',
            'click_num_show',
            'lesson_type_display',
            'status_display')

    def random_click_num(self, obj):
        """ 阅读人数(根据点击数量) """
        if obj.click_num > 400:
            return obj.click_num
        else:
            return max(obj.click_num, obj.order_weight * 10 + obj.order_weight * 3)


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

        



