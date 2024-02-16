import requests
import streamlit as st
from rich.console import Console

from helper import FASTAPI_URL

console = Console(tab_size=2)


st.set_page_config(page_title="Alt Texter: Add alt texts to your images", layout="wide")
st.title("Your Products")
st.markdown("Check your product descriptions and alt texts")

PLATFORMS = ["WooCommerce", "Shopify"]

placeholder = st.empty()

get_products_button = st.button("Get products")

if get_products_button:
    with placeholder.container():
        with st.status("Retrieving products"):
            products_response = requests.get(f"{FASTAPI_URL}/woocommerce/products")

    placeholder.empty()
    if products_response.status_code == 200:
        products = products_response.json()

        refresh_button = st.button("Refresh product data")

        products_lacking_alts = 0

        for product in products["data"]:
            # get total images and images without alts
            total_images = len(product["images"])
            images_without_alts = 0
            for image in product["images"]:
                if not image["alt"]:
                    images_without_alts += 1

            if images_without_alts > 0:
                products_lacking_alts += 1

            st.markdown("#### Summary")
            if products_lacking_alts:
                st.markdown(
                    f":warning: {products_lacking_alts} of your {len(products['data'])} products lack some or all alt texts for images. This is bad for SEO."
                )
            else:
                st.markdown(
                    ":partying_face: Congratulations! All your product images have alt texts!"
                )

            st.divider()

            col1, col2 = st.columns([1, 5])
            with col1:
                st.image(product["images"][0]["src"])
                if images_without_alts:
                    st.markdown(
                        f":warning: Images without alt texts: :red[**{images_without_alts}**]/{total_images}"
                    )
                else:
                    st.markdown(":white_check_mark: :green[All images have alt texts]")
            with col2:
                st.markdown(f"### {product['name']}")
                st.markdown("##### Description")
                st.markdown(product["description"])
                st.markdown("\n\n")
                st.markdown("##### Short description")
                st.markdown(product["short_description"])

            st.divider()
    else:
        st.json(products_response.json())
