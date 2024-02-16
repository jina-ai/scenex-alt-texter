from rich.console import Console

console = Console(tab_size=2)

import requests
import streamlit as st

FASTAPI_URL = "http://127.0.0.1:8000"

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
st.warning(
    "Shoptimizer is still under heavy development. Back up your data before using it!"
)

st.title("Shoptimizer")

PLATFORMS = ["WooCommerce", "Shopify"]

st.sidebar.title("Settings")


# Define settings
settings = {}
scenex_api_key = st.sidebar.text_input(
    label="SceneXplain API key",
    type="password",
    help="Get on SceneXplain's [API page](https://scenex.jina.ai)",
)
platform = st.sidebar.selectbox(label="Platform", options=PLATFORMS)
platform_settings = st.sidebar.container(border=True)
with st.sidebar.expander("More settings"):
    shops = ["WooCommerce", "Shopify"]
    settings["overwrite"] = st.checkbox(label="Overwrite existing alts")
    if platform in shops:
        settings["output_full_response"] = st.checkbox(label="Output full response")
        settings["write_desc"] = st.checkbox(label="Create product description")

        settings["overwrite_desc"] = st.checkbox(label="Overwrite product description")
# --- end settings

if platform == "WooCommerce":
    woocommerce_url = platform_settings.text_input(label="WooCommerce URL")
    woocommerce_consumer_key = platform_settings.text_input(
        label="WooCommerce consumer key"
    )
    woocommerce_consumer_secret = platform_settings.text_input(
        label="WooCommerce consumer secret", type="password"
    )
    # alt_texter = WooCommerceTagger(
    # scenex_api_key=scenex_api_key,
    # url=woocommerce_url,
    # woocommerce_consumer_key=woocommerce_consumer_key,
    # woocommerce_consumer_secret=woocommerce_consumer_secret,
    # write_desc=settings["write_desc"],
    # overwrite_desc=settings["overwrite_desc"],
    # )

elif platform == "Shopify":
    shopify_shop_name = platform_settings.text_input(label="Shopify shop name")
    shopify_access_token = platform_settings.text_input(
        label="Shopify access token", type="password"
    )
    # alt_texter = ShopifyHandler(
    # scenex_api_key=scenex_api_key,
    # url=None,
    # shopify_shop_name=shopify_shop_name,
    # shopify_access_token=shopify_access_token,
    # )


placeholder = st.empty()
with placeholder.container():
    st.markdown(
        "##### Use AI to write compelling SEO-friendly product descriptions and optimize your SEO by generating alt texts for your images"
    )

log_placeholder = st.empty()

button_col_1, button_col_2 = st.columns(2)

with button_col_1:
    check_products_button = st.button("Check products")

with button_col_2:
    optimize_button = st.button(label="Optimize SEO", type="primary")

if check_products_button:
    log_placeholder.empty()
    products_response = requests.get(f"{FASTAPI_URL}/woocommerce/products")
    if products_response.status_code == 200:
        products = products_response.json()
        for product in products["data"]:
            # get total images and images without alts
            total_images = len(product["images"])
            images_without_alts = 0
            for image in product["images"]:
                if not image["alt"]:
                    images_without_alts += 1

            if images_without_alts > 0:
                text_color = "red"
                emoji = ":warning:"
            else:
                text_color = "green"
                emoji = ":white_check_mark:"

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

    with log_placeholder.container():
        st.markdown(f"Out of {len(data['listings'])} products:")
        st.markdown(
            f"- **{data['stats']['no_alts']}** images need alt text.\n- The average description length is **{data['stats']['average_word_count']} words**"
        )

        console.print(data)
        st.dataframe(
            data["listings"],
            hide_index=True,
            column_config={
                # "image_url": "Image URL",
                "image_count": "Image count",
                "product_name": "Product name",
                "no_alts": "Images without alt text",
                "description_word_count": "Description word count",
                "description": "Description",
            },
        )


if optimize_button:
    placeholder.empty()
    log_placeholder.empty()
    counter = 0  # track count of updated items

    # if platform == "Ghost":
    # post_ids = alt_texter._get_post_ids()

    # status_indicator = st.status(
    # f"Processing {len(post_ids)} {platform} posts", expanded=True
    # )
    # with log_placeholder.container():
    # with status_indicator:
    # # with st.status(f"Processing {len(post_ids)} posts", expanded=True):
    # for post_id in post_ids:
    # post = alt_texter._get_post(post_id)
    # st.write(f":gear: Processing **{post['title']}**")
    # post_with_alts = alt_texter.add_alts(post_id)

    # if alt_texter._is_post_changed(post, post_with_alts):
    # st.write(f":arrow_up: Updating **{post['title']}** on Ghost")
    # alt_texter.update_post(post_id, post_with_alts)

    # counter += 1

    # elif platform == "WordPress":
    # status_indicator = st.status("Processing {platform} data", expanded=True)
    # wordpress_items = []
    # with log_placeholder.container():
    # with status_indicator:
    # for item_type in wordpress_item_types:
    # st.write(f":arrow_down: Retrieving WordPress {item_type}")
    # items = alt_texter._get_items(content_types=wordpress_item_types)
    # wordpress_items.extend(items)

    # for item in wordpress_items:
    # st.write(f":gear: Processing **{item['title']['rendered']}**")
    # updated_item_data = alt_texter.add_alts(item)
    # alt_texter.update_item(updated_item_data)
    # counter += 1

    # if platform == "WooCommerce":
    # status_indicator = st.status(f"Retrieving {platform} products", expanded=True)
    # with log_placeholder.container():
    # with status_indicator:
    # # with st.status("Processing WooCommerce data", expanded=True):
    # # st.write(":arrow_down: Retrieving products")
    # products = alt_texter.get_products()

    # status_indicator.update(label="Optimizing products")
    # for product in products:
    # st.write(f":gear: Processing **{product['name']}**")
    # st.write("- :frame_with_picture: Creating alts")
    # updated_alt_data = alt_texter.add_alts(product)
    # alt_texter.update_product(updated_alt_data)
    # st.write(
    # "- :lower_left_ballpoint_pen: Writing SEO-friendly description"
    # )
    # if settings["write_desc"] and platform in shops:
    # updated_desc_data = alt_texter.add_desc(product, overwrite=True)
    # alt_texter.update_product(product)
    # counter += 1

    # elif platform == "Shopify":
    # status_indicator = st.status(f"Processing {platform} data", expanded=True)
    # with log_placeholder.container():
    # with status_indicator:
    # # with st.status("Processing WooCommerce data", expanded=True):
    # products = alt_texter.get_products()

    # for product in products:
    # st.write(f":gear: Processing **{product['title']}**")
    # updated_alt_data = alt_texter.add_alts(product)
    # alt_texter.update_product(updated_alt_data)
    # counter += 1

    # placeholder.success(f":white_check_mark: All done! {counter} items processed.")
