import os

PLATFORM = os.environ.get("PLATFORM", "ghost")  # default to ghost for now
SCENEX_API_KEY = os.environ["SCENEX_API_KEY"]
SCENEX_URL = os.environ.get("SCENE_URL", "https://api.scenex.jina.ai/v1/describe")

if PLATFORM == "ghost":
    GHOST_BLOG_URL = os.environ["GHOST_BLOG_URL"]
    GHOST_API_KEY = os.environ["GHOST_API_KEY"]

    from helper import GhostTagger

    alt_texter = GhostTagger(
        scenex_api_key=SCENEX_API_KEY,
        scenex_url=SCENEX_URL,
        url=GHOST_BLOG_URL,
        ghost_api_key=GHOST_API_KEY,
    )

    alt_texter.update_all()

elif PLATFORM == "wordpress":
    WORDPRESS_URL = os.environ["WORDPRESS_URL"]
    WORDPRESS_USER = os.environ["WORDPRESS_USER"]
    WORDPRESS_PASSWORD = os.environ["WORDPRESS_PASSWORD"]

    from helper import WordPressTagger

    alt_texter = WordPressTagger(
        scenex_api_key=SCENEX_API_KEY,
        scenex_url=SCENEX_URL,
        wordpress_url=WORDPRESS_URL,
        wordpress_username=WORDPRESS_USER,
        wordpress_password=WORDPRESS_PASSWORD,
    )

    content_types = ["posts", "media", "pages"]

    content_objects = alt_texter._get_items(limit=10_000, content_types=content_types)

    for item in content_objects:
        updated_object = alt_texter.add_alts(content_object=item)
        response = alt_texter.update_item(updated_object)

elif PLATFORM == "woocommerce":
    WOOCOMMERCE_URL = os.environ["WOOCOMMERCE_URL"]
    WOOCOMMERCE_KEY = os.environ["WOOCOMMERCE_KEY"]
    WOOCOMMERCE_SECRET = os.environ["WOOCOMMERCE_SECRET"]

    from helper import WooCommerceTagger

    alt_texter = WooCommerceTagger(
        url=WOOCOMMERCE_URL,
        woocommerce_consumer_key=WOOCOMMERCE_KEY,
        woocommerce_consumer_secret=WOOCOMMERCE_SECRET,
        scenex_api_key=SCENEX_API_KEY,
    )

    alt_texter.update_products()

elif PLATFORM == "shopify":
    SHOPIFY_SHOP_NAME = os.environ["SHOPIFY_SHOP_NAME"]
    SHOPIFY_ACCESS_TOKEN = os.environ["SHOPIFY_ACCESS_TOKEN"]

    from helper import ShopifyHandler

    alt_texter = ShopifyHandler(
        url="foo.com",
        scenex_api_key=SCENEX_API_KEY,
        shopify_shop_name=SHOPIFY_SHOP_NAME,
        shopify_access_token=SHOPIFY_ACCESS_TOKEN,
    )

    alt_texter.update_products()
