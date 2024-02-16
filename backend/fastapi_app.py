import os

from creds import SCENEX_API_KEY, WooCommerceCreds
from fastapi import FastAPI
from helper import WooCommerceTagger
from rich.console import Console

console = Console()
app = FastAPI()

handler = WooCommerceTagger(
    scenex_api_key=SCENEX_API_KEY,
    url=WooCommerceCreds.WORDPRESS_URL,
    woocommerce_consumer_key=WooCommerceCreds.WOOCOMMERCE_KEY,
    woocommerce_consumer_secret=WooCommerceCreds.WOOCOMMERCE_SECRET,
)


class WooCommerce:
    @app.get("/woocommerce/products")
    def get_products():
        products = handler.get_products()

        return {"data": products}

    @app.get("/woocommerce/products/{product_id}")
    def get_product(product_id: str):
        product = handler.get_product(product_id)

        return {"data": product}

    @app.put("/woocommerce/products/{product_id}/update")
    def update_product(data_dict: dict):
        updated_product = handler.update_product(product=data_dict)

        # return {"product": updated_product}

    @app.get("/woocommerce/products/{product_id}/alts/create")
    def create_alts(product_id: str, overwrite: bool = False):
        product = handler.get_product(product_id)
        alt_data = handler.add_alts(product, overwrite=overwrite)

        if alt_data["updated_alts_count"] == 0:
            message = f"Skipping {product['name']}. All images have alt texts."
        else:
            message = f"Generated {alt_data['updated_alts_count']} alt texts for {product['name']}."

        return {
            "data": alt_data,
            "message": message,
        }

    @app.get("/woocommerce/products/{product_id}/desc/create")
    def create_description(product_id: str, overwrite: bool = False):
        product = handler.get_product(product_id)
        desc_data = handler.add_desc(product=product, overwrite=overwrite)

        return {"data": desc_data}


if __name__ == "__main__":
    PLATFORM = os.environ.get(
        "SHOPIFY_PLATFORM", "woocommerce"
    )  # default to ghost for now
    SCENEX_API_KEY = os.environ["SCENEX_API_KEY"]
    SCENEX_URL = os.environ.get("SCENE_URL", "https://api.scenex.jina.ai/v1/describe")

    # if PLATFORM == "ghost":
    # GHOST_BLOG_URL = os.environ["GHOST_BLOG_URL"]
    # GHOST_API_KEY = os.environ["GHOST_API_KEY"]

    # from helper import GhostTagger

    # alt_texter = GhostTagger(
    # scenex_api_key=SCENEX_API_KEY,
    # scenex_url=SCENEX_URL,
    # url=GHOST_BLOG_URL,
    # ghost_api_key=GHOST_API_KEY,
    # )

    # alt_texter.update_all()

    # elif PLATFORM == "wordpress":
    # WORDPRESS_URL = os.environ["WORDPRESS_URL"]
    # WORDPRESS_USER = os.environ["WORDPRESS_USER"]
    # WORDPRESS_PASSWORD = os.environ["WORDPRESS_PASSWORD"]

    # from helper import WordPressTagger

    # alt_texter = WordPressTagger(
    # scenex_api_key=SCENEX_API_KEY,
    # scenex_url=SCENEX_URL,
    # wordpress_url=WORDPRESS_URL,
    # wordpress_username=WORDPRESS_USER,
    # wordpress_password=WORDPRESS_PASSWORD,
    # )

    # content_types = ["posts", "media", "pages"]

    # content_objects = alt_texter._get_items(limit=10_000, content_types=content_types)

    # for item in content_objects:
    # updated_object = alt_texter.add_alts(content_object=item)
    # response = alt_texter.update_item(updated_object)

    if PLATFORM == "woocommerce":
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
