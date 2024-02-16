import os

import streamlit as st
from rich.console import Console

console = Console(tab_size=2)

# scenex
SCENEX_API_KEY = os.environ.get("SCENEX_API_KEY", "")

# woocommerce
WOOCOMMERCE_URL = os.environ.get("WOOCOMMERCE_URL", "")
WOOCOMMERCE_KEY = os.environ.get("WOOCOMMERCE_KEY", "")
WOOCOMMERCE_SECRET = os.environ.get("WOOCOMMERCE_SECRET", "")

# shopify
SHOPIFY_SHOP_NAME = os.environ.get("SHOPIFY_SHOP_NAME", "")
SHOPIFY_ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")


# Ugh, none of these seem to get persisted

st.title("Configure Shoptimize")
st.markdown(
    "API keys, URLs, and more. For optimization settings, check the 'Optimize Products' page."
)

PLATFORMS = ["WooCommerce", "Shopify"]

# if "scenex_api_key" not in st.session_state:
# st.session_state["scenex_api_key"] = ""


scenex_api_key = st.text_input(
    label="SceneXplain API key",
    type="password",
    value=SCENEX_API_KEY,
    help="Get on SceneXplain's [API page](https://scenex.jina.ai)",
)


platform = st.selectbox(label="Platform", options=PLATFORMS)
platform_settings = st.container(border=True)

if platform == "WooCommerce":
    woocommerce_url = platform_settings.text_input(
        label="WooCommerce URL", value=WOOCOMMERCE_URL
    )
    woocommerce_consumer_key = platform_settings.text_input(
        label="WooCommerce consumer key", value=WOOCOMMERCE_KEY
    )
    woocommerce_consumer_secret = platform_settings.text_input(
        label="WooCommerce consumer secret", type="password", value=WOOCOMMERCE_SECRET
    )

elif platform == "Shopify":
    shopify_shop_name = platform_settings.text_input(
        label="Shopify shop name", value=SHOPIFY_SHOP_NAME
    )
    shopify_access_token = platform_settings.text_input(
        label="Shopify access token", type="password", value=SHOPIFY_ACCESS_TOKEN
    )

save_button = st.button("Save")

if save_button:
    # st.session_state["scenex_api_key"] = scenex_api_key
    os.environ["SCENEX_API_KEY"] = scenex_api_key
    if platform == "WooCommerce":
        os.environ["WOOCOMMERCE_URL"] = woocommerce_url
        os.environ["WOOCOMMERCE_KEY"] = woocommerce_consumer_key
        os.environ["WOOCOMMERCE_SECRET"] = woocommerce_consumer_secret

    # shopify
    elif platform == "Shopify":
        os.environ["SHOPIFY_SHOP_NAME"] = shopify_shop_name
        os.environ["SHOPIFY_ACCESS_TOKEN"] = shopify_access_token

    st.toast("Settings saved!", icon="💾")
