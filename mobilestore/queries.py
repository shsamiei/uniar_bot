from .models import Brand, Mobile


def list_all_brands():
    query = Brand.objects.all()
    return query


def list_all_mobiles():
    query = ...
    return query


def price_of_mobile_with_model(model):
    query = ...
    return query


def most_expensive_mobile():
    query = ...
    return query


def all_mobiles_with_brand_of(brand_name):
    query = ...
    return query


def all_available_mobiles_with_price_in_range(min_price, max_price):
    query = ...
    return query
