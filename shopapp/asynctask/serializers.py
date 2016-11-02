from shopapp.asynctask.models import PrintAsyncTaskModel
from rest_framework import serializers


class PrintAsyncTaskModeSerializer(serializers.ModelSerializer):
    class Meta:
        # model = PrintAsyncTaskModel
        # fields = ('task_id ', 'task_type', 'operator', 'file_path_to', ' created',"modified","status","params")
        exclude = ('url',)

        # class AsyncCategoryModeSerializer(serializers.ModelSerializer):
        # class Meta:
        # model = PrintAsyncTaskModel
        # fields = ('task_id ', 'task_type', 'operator', 'file_path_to', ' created',"modified","status","params")
