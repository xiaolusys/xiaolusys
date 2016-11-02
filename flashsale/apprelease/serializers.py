from rest_framework import serializers
from flashsale.apprelease.models import AppRelease
from flashsale.apprelease import constants


class AppReleaseSerialize(serializers.ModelSerializer):
    ios_qrcode_link = serializers.SerializerMethodField('qrcode_link_func', read_only=True)
    ios_download_link = serializers.SerializerMethodField('download_link_func', read_only=True)

    class Meta:
        model = AppRelease
        fields = (
            "download_link",
            "qrcode_link",
            "ios_qrcode_link",
            "ios_download_link",
            "version",
            "status",
            "release_time",
            'status',
            'release_time',
            'auto_update',
            'hash_value',
            'version_code',
            "memo")

    def qrcode_link_func(self, obj):
        return constants.APP_STORE_DOWNLOAD_QRCODE

    def download_link_func(self, obj):
        return constants.APP_STORE_DOWNLOAD

