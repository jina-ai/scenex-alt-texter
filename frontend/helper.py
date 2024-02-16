import os


def get_settings():
    settings = {
        "scenex_api_key": os.environ.get("scenex_api_key", ""),
        "woocommerce_url": os.environ.get("woocommerce_url", ""),
        "woocommerce_key": os.environ.get("woocommerce_key", ""),
        "woocommerce_secret": os.environ.get("woocommerce_secret", ""),
        "shopify_shop_name": os.environ.get("shopify_shop_name", ""),
        "shopify_access_token": os.environ.get("shopify_access_token", ""),
    }

    return settings
