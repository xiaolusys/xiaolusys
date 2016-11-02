
from django.core.cache import cache

API_CACHE_TIMEOUT = 7 * 24 * 3600

def get_model_by_id(filters, model_class):
    """ eg: filters = {'id':1} """
    filter_name, model_id = filters.items()[0]
    cache_key = model_class.API_CACHE_KEY_TPL.format(model_id)
    cache_value = cache.get(cache_key)
    if not cache_value:
        instance = model_class.objects.get(**filters)
        cache_value = instance.to_apimodel()
        cache.set(cache_key, cache_value, API_CACHE_TIMEOUT)
    return cache_value

def get_multi_model_by_ids(filters, model_class):
    """ eg: filters = {'id': [1,2,3]} """
    filter_name, model_ids = filters.items()[0]
    fetch_keys = map(model_class.API_CACHE_KEY_TPL.format, model_ids)
    cache_results = cache.get_many(fetch_keys)
    cache_values  = []
    # return results by input ids order
    for model_id, cache_key in zip(model_ids, fetch_keys):
        cache_value = cache_results.get(cache_key)
        if not cache_value:
            try:
                cache_value = get_model_by_id({filter_name: model_id}, model_class)
            except model_class.DoesNotExist:
                continue

        if cache_value:
            cache_values.append(cache_value)

    return cache_values