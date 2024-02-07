import time

import streamlit as st

from helper import (GhostTagger, ShopifyHandler, WooCommerceTagger,
                    WordPressTagger)

all_done_message = "All done"

st.title("Alt Texter")
st.subheader("Add alt texts to your images")

PLATFORMS = ["Ghost", "WordPress", "WooCommerce", "Shopify"]

st.sidebar.title("Settings")
scenex_api_key = st.sidebar.text_input(
    label="SceneXplain API key",
    type="password",
    help="Get on SceneXplain's [API page](https://scenex.jina.ai)",
)

platform = st.sidebar.selectbox(label="Platform", options=PLATFORMS)

settings = st.sidebar.container(border=True)
if platform == "Ghost":
    ghost_url = settings.text_input(label="Ghost blog URL")
    ghost_api_key = settings.text_input(label="Ghost Admin API key", type="password")

elif platform == "WordPress":
    item_types = ["posts", "pages", "media"]
    wordpress_url = settings.text_input(label="WordPress URL")
    wordpress_username = settings.text_input(label="WordPress username")
    wordpress_password = settings.text_input(
        label="WordPress password", type="password"
    )
    wordpress_item_types = settings.multiselect(
        label="Content types", options=item_types, default=item_types
    )

elif platform == "WooCommerce":
    woocommerce_url = settings.text_input(label="WooCommerce URL")
    woocommerce_consumer_key = settings.text_input(label="WooCommerce consumer key")
    woocommerce_consumer_secret = settings.text_input(
        label="WooCommerce consumer secret", type="password"
    )

elif platform == "Shopify":
    shopify_shop_name = settings.text_input(label="Shopify shop name")
    shopify_access_token = settings.text_input(
        label="Shopify access token", type="password"
    )

run_button = st.sidebar.button(label="Run")

status_placeholder = st.empty()

if run_button:
    counter = 0
    if platform == "Ghost":
        alt_texter = GhostTagger(
            scenex_api_key=scenex_api_key,
            url=ghost_url,
            ghost_api_key=ghost_api_key,
        )

        post_ids = alt_texter._get_post_ids()

        with st.status(f"Processing {len(post_ids)} posts", expanded=True):
            for post_id in post_ids:
                post = alt_texter._get_post(post_id)
                st.write(f":gear: Processing **{post['title']}**")
                # with st.spinner(f"Processing {post['title']}"):
                # time.sleep(5)
                post_with_alts = alt_texter.add_alts(post_id)

                if alt_texter._is_post_changed(post, post_with_alts):
                    # with st.spinner(f"Updating {post['title']} on Ghost"):
                    st.write(f":arrow_up: Updating **{post['title']}** on Ghost")
                    alt_texter.update_post(post_id, post_with_alts)

                counter += 1

    elif platform == "WordPress":
        alt_texter = WordPressTagger(
            scenex_api_key=scenex_api_key,
            wordpress_url=wordpress_url,
            wordpress_username=wordpress_username,
            wordpress_password=wordpress_password,
        )

        wordpress_items = []
        for item_type in wordpress_item_types:
            with st.spinner(f"Retrieving WordPress {item_type}"):
                items = alt_texter._get_items(content_types=wordpress_item_types)
                wordpress_items.append(items)

        for item in items:
            with st.spinner(f"Processing {item['title']['rendered']}"):
                updated_item_data = alt_texter.add_alts(item)
                alt_texter.update_item(updated_item_data)
                counter += 1

    elif platform == "WooCommerce":
        alt_texter = WooCommerceTagger(
            scenex_api_key=scenex_api_key,
            woocommerce_url=woocommerce_url,
            woocommerce_consumer_key=woocommerce_consumer_key,
            woocommerce_consumer_secret=woocommerce_consumer_secret,
        )

        with st.spinner("Retrieving products"):
            products = alt_texter.get_products()

        for product in products:
            with st.spinner(f"Processing {product['name']}"):
                updated_product_data = alt_texter.add_alts(product)
                alt_texter.update_product(updated_product_data)
                counter += 1

    elif platform == "Shopify":
        alt_texter = ShopifyHandler(
            scenex_api_key=scenex_api_key,
            url=None,
            shopify_shop_name=shopify_shop_name,
            shopify_access_token=shopify_access_token,
        )

        with st.spinner("Retrieving products"):
            products = alt_texter.get_products()

        for product in products:
            with st.spinner(f"Processing {product['title']}"):
                updated_product_data = alt_texter.add_alts(product)
                alt_texter.update_product(updated_product_data)
                counter += 1

    status_placeholder.success(f"All done! {counter} items processed.")
