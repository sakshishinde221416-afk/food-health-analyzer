from .models import Product
from .views import fetch_product_from_open_food_facts


def get_or_fetch_product(barcode):
    """
    Find product by barcode in PostgreSQL database.
    If missing, fetch from Open Food Facts API, save to DB, and return.
    Returns tuple: (product, source_string) or (None, None).
    """
    try:
        product = Product.objects.get(barcode=barcode)
        return product, "database"
    except Product.DoesNotExist:
        pass

    product = fetch_product_from_open_food_facts(barcode)
    if product:
        return product, "open_food_facts"

    return None, None
