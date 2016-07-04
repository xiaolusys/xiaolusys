# coding:utf8

from django.forms import model_to_dict


def get_forecastinbound_data(forecast_id):
    from flashsale.forecast.models import ForecastInbound
    fibound = ForecastInbound.objects.filter(id=forecast_id).first()
    if fibound:
        return model_to_dict(fibound)
    return {}