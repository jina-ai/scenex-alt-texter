import requests
import streamlit as st
from rich.console import Console

from helper import FASTAPI_URL

console = Console(tab_size=2)


st.set_page_config(page_title="Alt Texter: Add alt texts to your images", layout="wide")

st.title("Optimize Products")
st.markdown(
    "Optimize your products' alt texts and descriptions for better SEO and accessibility"
)

PLATFORMS = ["WooCommerce", "Shopify"]

options = {}

placeholder = st.empty()

options_expander = st.expander("Options", expanded=True)
with options_expander:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### Image alt texts")
        options["generate_alts"] = st.checkbox(
            label="Create alt texts for product images", value=True
        )
        options["overwrite_alts"] = st.checkbox(label="Overwrite existing alt texts")

    with col2:
        st.markdown("#### Descriptions")
        options["generate_desc"] = st.checkbox(
            label="Create product description", value=True
        )
        options["overwrite_desc"] = st.checkbox(
            label="Overwrite existing product description"
        )

    with col3:
        st.markdown("#### Misc")
        options["dry_run"] = st.checkbox(label="Dry run")

    if options["generate_desc"] or options["generate_alts"]:
        disabled_state = False
    else:
        disabled_state = True

    optimize_button = st.button(
        "Optimize products", type="primary", disabled=disabled_state
    )

if optimize_button:
    with st.spinner("Getting products"):
        products_response = requests.get(f"{FASTAPI_URL}/woocommerce/products")

    if products_response.status_code == 200:
        products = products_response.json()

    progress_bar = st.progress(0, text=products["data"][0]["name"])
    progress_step = float(1 / len(products["data"]))

    with st.status("Processing products"):
        for i, product in enumerate(products["data"], start=1):
            st.markdown(f"**{product['name']}**")
            progress_bar.progress(i * progress_step, text=f"{product['name']}")

            updated_product = {}
            if options["generate_alts"]:
                url = f"{FASTAPI_URL}/woocommerce/products/{product['id']}/alts/create"
                if options["overwrite_alts"]:
                    url = url + "?overwrite=true"

                alts_response = requests.get(url)
                alts_response_dict = alts_response.json()
                st.markdown("Updating image alt texts")

                if alts_response_dict["data"]["updated_alts_count"] > 0:
                    updated_product.update(alts_response_dict["data"])

            if options["generate_desc"]:
                url = f"{FASTAPI_URL}/woocommerce/products/{product['id']}/desc/create"
                if options["overwrite_desc"]:
                    url = url + "?overwrite=true"

                # st.write("Updating descriptions")
                st.markdown("Updating description")
                desc_response = requests.get(url)
                desc_response_dict = desc_response.json()

                if "description" in desc_response_dict["data"]:
                    updated_product.update(desc_response_dict["data"])

            # try:
            # # show name of next product as soon as progress done for this one
            # progress_bar.progress(i * progress_step, text=f"{product['name']}")
            # except:
            # progress_bar.progress(i * progress_step, text="Done")
            # progress_bar.progress(1, text=f"{product['name']}")

            # st.json(updated_product)

            if updated_product:
                st.markdown(f"##### {product['name']}")

                if "images" in updated_product:
                    img_list = updated_product["images"]
                    alt_text_color = "green"
                else:
                    img_list = product["images"]
                    alt_text_color = "grey"

                if "description" in updated_product:
                    desc_field = updated_product["description"]
                    desc_text_color = "green"
                else:
                    desc_field = product["description"]
                    desc_text_color = "grey"

                feat_img_col, detail_col = st.columns([1, 7])
                with feat_img_col:
                    st.image(img_list[0]["src"])
                with detail_col:
                    st.markdown(f":{desc_text_color}[{desc_field}]")

                st.markdown("###### Alt texts")
                for image in img_list:
                    img_col, alt_col = st.columns([1, 11])
                    with img_col:
                        st.image(image["src"])
                    with alt_col:
                        st.write(f":{alt_text_color}[{image['alt']}]")

                st.divider()

            if not options["dry_run"]:
                if (
                    "images" in updated_product.keys()
                    or "description" in updated_product.keys()
                ):
                    url = f"{FASTAPI_URL}/woocommerce/products/{product['id']}/update"
                    st.write(f"Updating {product['name']}")
                    update_response = requests.put(url, json=updated_product)

        st.write("All done!")
