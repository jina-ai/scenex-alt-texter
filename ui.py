import time

import streamlit as st

from helper import (GhostTagger, ShopifyHandler, WooCommerceTagger,
                    WordPressTagger)

help_markdown = """
Alt Texter automatically adds alt tags to all the images (including featured images) on your blog using [SceneXplain](https://scenex.jina.ai).

### How does it work?

Alt Texter will:

- Download each content item from whatever platform you're using
- Check each image to see if it has alt text:
    - If yes, skip that image
    - If no, create an alt text using SceneXplain and write that to the content data
- Check if the content has new alt texts:
    - If yes, update the content
    - If no, skip update
"""

st.set_page_config(page_title="Alt Texter: Add alt texts to your images", layout="wide")

st.title("Alt Texter")

PLATFORMS = ["Ghost", "WordPress", "WooCommerce", "Shopify"]

st.warning(
    "Alt Texter is still under heavy development. Back up your data before using it!"
)
st.sidebar.title("Settings")

# place holder for status message at end of run
placeholder = st.empty()
with placeholder.container():
    st.markdown(help_markdown)

log_placeholder = st.empty()

# Define settings
scenex_api_key = st.sidebar.text_input(
    label="SceneXplain API key",
    type="password",
    help="Get on SceneXplain's [API page](https://scenex.jina.ai)",
)
platform = st.sidebar.selectbox(label="Platform", options=PLATFORMS)
platform_settings = st.sidebar.container(border=True)
if platform == "Ghost":
    ghost_url = platform_settings.text_input(label="Ghost blog URL")
    ghost_api_key = platform_settings.text_input(
        label="Ghost Admin API key", type="password"
    )

elif platform == "WordPress":
    item_types = ["posts", "pages"]
    wordpress_url = platform_settings.text_input(label="WordPress URL")
    wordpress_username = platform_settings.text_input(label="WordPress username")
    wordpress_password = platform_settings.text_input(
        label="WordPress application password",
        type="password",
        help="You need to set a dedicated [application password](https://wordpress.com/support/security/two-step-authentication/application-specific-passwords/). Your usual login password won't work.",
    )
    wordpress_item_types = platform_settings.multiselect(
        label="Content types", options=item_types, default=item_types
    )

elif platform == "WooCommerce":
    woocommerce_url = platform_settings.text_input(label="WooCommerce URL")
    woocommerce_consumer_key = platform_settings.text_input(
        label="WooCommerce consumer key"
    )
    woocommerce_consumer_secret = platform_settings.text_input(
        label="WooCommerce consumer secret", type="password"
    )

elif platform == "Shopify":
    shopify_shop_name = platform_settings.text_input(label="Shopify shop name")
    shopify_access_token = platform_settings.text_input(
        label="Shopify access token", type="password"
    )

# --- end settings

run_button = st.sidebar.button(label="Run")


if run_button:
    placeholder.empty()
    log_placeholder.empty()
    counter = 0  # track count of updated items

    if platform == "Ghost":
        alt_texter = GhostTagger(
            scenex_api_key=scenex_api_key,
            url=ghost_url,
            ghost_api_key=ghost_api_key,
        )

        post_ids = alt_texter._get_post_ids()

        status_indicator = st.status(
            f"Processing {len(post_ids)} {platform} posts", expanded=True
        )
        with log_placeholder.container():
            with status_indicator:
                # with st.status(f"Processing {len(post_ids)} posts", expanded=True):
                for post_id in post_ids:
                    post = alt_texter._get_post(post_id)
                    st.write(f":gear: Processing **{post['title']}**")
                    post_with_alts = alt_texter.add_alts(post_id)

                    if alt_texter._is_post_changed(post, post_with_alts):
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

        status_indicator = st.status("Processing {platform} data", expanded=True)
        wordpress_items = []
        with log_placeholder.container():
            with status_indicator:
                for item_type in wordpress_item_types:
                    st.write(f":arrow_down: Retrieving WordPress {item_type}")
                    items = alt_texter._get_items(content_types=wordpress_item_types)
                    wordpress_items.extend(items)

                for item in wordpress_items:
                    st.write(f":gear: Processing **{item['title']['rendered']}**")
                    updated_item_data = alt_texter.add_alts(item)
                    alt_texter.update_item(updated_item_data)
                    counter += 1

    elif platform == "WooCommerce":
        alt_texter = WooCommerceTagger(
            scenex_api_key=scenex_api_key,
            url=woocommerce_url,
            woocommerce_consumer_key=woocommerce_consumer_key,
            woocommerce_consumer_secret=woocommerce_consumer_secret,
        )

        status_indicator = st.status(f"Processing {platform} data", expanded=True)
        with log_placeholder.container():
            with status_indicator:
                # with st.status("Processing WooCommerce data", expanded=True):
                st.write(":arrow_down: Retrieving products")
                products = alt_texter.get_products()

                for product in products:
                    st.write(f":gear: Processing **{product['name']}**")
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

        status_indicator = st.status(f"Processing {platform} data", expanded=True)
        with log_placeholder.container():
            with status_indicator:
                # with st.status("Processing WooCommerce data", expanded=True):
                products = alt_texter.get_products()

                for product in products:
                    st.write(f":gear: Processing **{product['title']}**")
                    updated_product_data = alt_texter.add_alts(product)
                    alt_texter.update_product(updated_product_data)
                    counter += 1

    placeholder.success(f":white_check_mark: All done! {counter} items processed.")
