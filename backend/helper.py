import base64
import json
import logging
# import tempfile
# import os
import time
from difflib import unified_diff

import jwt
import requests
# import shopify
from bs4 import BeautifulSoup
# from lxml.html import diff, fromstring, tostring
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.logging import RichHandler
from woocommerce import API

console = Console(tab_size=2)

FASTAPI_URL = "http://127.0.0.1:8000"

# set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

SCENEX_URL = "https://api.scenex.jina.ai/v1/describe"


class AltTexter:
    def __init__(
        self,
        url: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
        language: str = "en",
        overwrite_alts: bool = False,
    ):
        self.scenex_headers = {
            "x-api-key": f"token {scenex_api_key}",
            "content-type": "application/json",
        }
        self.url = url
        self.scenex_url = scenex_url
        self.language = language
        self.overwrite_alts = overwrite_alts

    def send_scenex_request(self, data: dict):
        response = requests.post(
            url=self.scenex_url, headers=self.scenex_headers, json=data
        )

        return response.json()

    def generate_alt_text(
        self,
        image_url: str,
        max_length: int = 125,
        max_tries: int = 3,
        language: str = "en",
    ):
        """
        Generate alt text for a given image.

        Args:
            image_url (str): URL of the image. Can be 'standard' URL or a datauri
            max_length (int): Maximum length of the alt text. Defaults to 125, which is a recommended standard.
            max_tries (int): Maximum attempts to generate image before giving up.

        Returns:
            alt_text (str): The alt text of the input image URL.
        """
        # if self._validate_image(image_url):

        filename = image_url.split("/")[-1]
        data = {
            "data": [
                {
                    "task_id": "alt_text",
                    "image": image_url,
                    "languages": [self.language],
                }
            ]
        }

        # implement max tries since sometimes SX has issues
        alt_text = None
        alt_text_tries = 0

        while (not alt_text) and (alt_text_tries < max_tries):
            log.info(f"Sending {filename} to SceneXplain")
            response = requests.post(
                url=self.scenex_url, headers=self.scenex_headers, json=data
            )
            alt_text = response.json()["result"][0]["text"][:max_length]
            alt_text_tries += 1
        # except Exception as e:
        # # console.print(e)
        # log.error(e)

        return alt_text
        # else:
        # return

    def _validate_image(self, image_url: str):
        """
        Validate image URL:
            - Check file extension is supported.
            - Check that URL resolves.

        Args:
            image_url (str): The URL of the image.
        """
        supported_formats = ["gif", "jpeg", "jpg", "png", "webp"]
        if not image_url.startswith("data"):
            filename = image_url.split("/")[-1]
            file_ext = filename.split(".")[-1].lower()
            if file_ext not in supported_formats:
                log.warn(f"{filename} is not in supported format.")
                return False

            response = requests.get(image_url)
            status_code = response.status_code
            if status_code != 200:
                log.warn(
                    f"{filename} could not be downloaded. Status code {status_code}"
                )
                return False

        return True


# class GhostTagger(AltTexter):
# def __init__(
# self,
# url: str,
# ghost_api_key: str,
# scenex_api_key: str,
# scenex_url: str = SCENEX_URL,
# language: str = "en",
# ):
# super().__init__(url, scenex_api_key, scenex_url, language)
# self.ghost_api_key = ghost_api_key
# self.ghost_url = url
# self.scenex_url = scenex_url

# def _get_ghost_token(self, ghost_api_key: str):
# """
# Get a Ghost token from API key

# Args:
# ghost_api_key (str): Your Ghost Admin API key.

# Returns:
# token: Resulting Ghost token.
# """
# api_id, api_secret = ghost_api_key.split(":")

# payload = {
# "iat": int(time.time()),
# "exp": int(time.time()) + 300,
# "aud": "/admin/",
# }

# token = jwt.encode(
# payload,
# bytes.fromhex(api_secret),
# algorithm="HS256",
# headers={"kid": api_id},
# )

# return token

# def _renew_headers(self, ghost_api_key: str) -> dict:
# """
# Ghost tokens expire after a while. This function recreates the token and returns updated headers.

# Args:
# ghost_api_key (str): Your Ghost Admin API key.

# Returns:
# ghost_headers (dict): Updated Ghost headers.
# """
# ghost_headers = {
# "Authorization": f"Ghost {self._get_ghost_token(ghost_api_key)}",
# "Content-Type": "application/json",
# }

# return ghost_headers

# def _get_post_ids(
# self,
# status: str = "published",
# limit: int = 10_000,
# order: str = "published_at desc",
# ) -> list:
# """
# Get IDs of all posts in Ghost blog.

# Args:
# status (str): published/scheduled/draft.
# limit (int): maximum number of post ids to retrieve.
# order (str): ordering method to use, followed by 'asc' (ascending) or 'desc' (descending).

# Returns:
# post_ids (list): a list of strings, where each string is a separate post.id.
# """
# ghost_headers = self._renew_headers(self.ghost_api_key)

# params = {
# "filter": f"status:{status}",
# "limit": limit,
# "order": order,
# "fields": "id",
# }

# response = requests.get(
# f"{self.ghost_url}/ghost/api/admin/posts/",
# headers=ghost_headers,
# params=params,
# )

# log.info("Getting Ghost post IDs")
# if response.status_code == 200:
# posts_data = response.json()
# post_ids = [post["id"] for post in posts_data["posts"]]
# else:
# log.error(f"Failed to retrieve posts: {response.text}")

# return post_ids

# def _get_post(self, post_id: str) -> dict:
# """
# Get an individual Ghost blog post.

# Args:
# post_id (str): Post ID of the post you wish to retrieve.

# Returns:
# post (dict): The post with the post ID you requested.
# """
# url = f"{self.ghost_url}/ghost/api/admin/posts/{post_id}"

# ghost_headers = self._renew_headers(self.ghost_api_key)
# response = requests.get(
# url, headers=ghost_headers, params={"formats": "lexical"}
# )

# if response.status_code == 200:
# post_data = response.json()
# post = post_data["posts"][0]
# return post
# else:
# log.error(f"Failed to retrieve post with ID {post_id}")
# return response.json()
# # return f"Error: {response.status_code}"

# def _get_posts(
# self,
# post_ids=[],
# status: str = "published",
# limit: int = 10_000,
# order: str = "published_at desc",
# ) -> list:
# """
# Get all posts in Ghost blog.

# Args:
# post_ids (list): list of post IDs to retrieve. If unset, retrieve 10,000.
# status (str): published/scheduled/draft.
# limit (int): maximum number of post ids to retrieve.
# order (str): ordering method to use, followed by 'asc' (ascending) or 'desc' (descending).

# Returns:
# post_ids (list): a list of strings, where each string is a separate post.id.
# """
# if not post_ids:
# post_ids = self._get_post_ids(status, limit, order)

# posts = [self._get_post(post_id) for post_id in post_ids]

# return posts

# def update_post(self, post_id, post_data) -> dict:
# """
# Update an individual Ghost blog post.

# Args:
# post_id (str): Post ID of the post you wish to update.
# post_data (dict): The updated post content you wish to write.

# Returns:
# response.json(): The updated post
# """
# url = f"{self.ghost_url}ghost/api/admin/posts/{post_id}/"
# data = {"posts": [post_data]}

# ghost_headers = self._renew_headers(self.ghost_api_key)
# log.info("Sending updated post to Ghost")
# response = requests.put(url, headers=ghost_headers, json=data)

# return response.json()

# def add_alts(self, post_id, max_tries=3) -> dict:
# """
# Add alt texts for all images in an individual Ghost post.

# Args:
# post_id (str): Post ID of the post you wish to add alts for.
# max_tries (int): How many times to try generating an alt text before giving up.

# Returns:
# post (dict): post (based on post_id arg) updated with alt texts.
# """
# post = self._get_post(post_id)
# log.info(f"Processing {post['title']}")

# # Process featured image
# if not post["feature_image_alt"]:
# alt_text = self.generate_alt_text(post["feature_image"])
# if alt_text:
# post["feature_image_alt"] = alt_text[:125]  # Ghost has hard limit here

# # Process post body
# if post["lexical"]:
# post["lexical"] = json.loads(post["lexical"])
# self.add_alt_text_recursive(post["lexical"]["root"]["children"])
# post["lexical"] = json.dumps(post["lexical"])

# return post

# def add_alt_text_recursive(self, rows) -> None:
# """
# Recurse through all nested structures in an individual Ghost blog post and add alt texts.
# """
# for row in rows:
# if row.get("type") == "image":
# if "alt" not in row:  # older posts don't even have the alt field
# row["alt"] = None
# if not row["alt"]:
# alt_text = self.generate_alt_text(row["src"])
# row["alt"] = alt_text

# # Recursively process nested rows
# if "children" in row and isinstance(row["children"], list):
# self.add_alt_text_recursive(row["children"])

# def _is_post_changed(self, original_post, new_post) -> bool:
# """
# Check if post content has been updated. Checks post content and featured image.

# Args:
# original_post (dict): Original Ghost blog post.
# new_post (dict): Updated version of Ghost blog post, relative to original.

# Returns:
# True if original_post and new_post are different.
# False if original_post and new_post are the same.
# """
# if new_post["lexical"]:
# if json.loads(original_post["lexical"]) != json.loads(new_post["lexical"]):
# return True

# if new_post["feature_image_alt"]:
# if original_post["feature_image_alt"] != new_post["feature_image_alt"]:
# return True

# return False

# def update_all(self, post_ids: list = []) -> None:
# """
# Create alt texts for all blog posts and write to Ghost.
# """
# if not post_ids:
# post_ids = self._get_post_ids()

# for post_id in post_ids:
# original_post = self._get_post(post_id)
# updated_post = self.add_alts(post_id)
# if self._is_post_changed(original_post, updated_post):
# self.update_post(post_id=post_id, post_data=updated_post)
# log.info("All done!")


class WooCommerceTagger(AltTexter):
    def __init__(
        self,
        url: str,
        woocommerce_consumer_key: str,
        woocommerce_consumer_secret: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
        write_desc: bool = False,
        overwrite_desc: bool = False,
    ):
        self.wcapi = API(
            url=url,
            consumer_key=woocommerce_consumer_key,
            consumer_secret=woocommerce_consumer_secret,
            version="wc/v3",
        )
        self.write_desc = write_desc
        self.overwrite_desc = overwrite_desc
        super().__init__(self, scenex_url=scenex_url, scenex_api_key=scenex_api_key)

    def get_products(self):
        """
        Get list of all WooCommerce products.
        """
        log.info("Getting WooCommerce products")
        products = self.wcapi.get("products").json()

        return products

    def get_product(self, product_id):
        product = self.wcapi.get(f"products/{product_id}").json()

        return product

    def products_to_table(self, products):
        """
        Create table of products for quick analysis of SEO
        """
        output = {}
        output["listings"] = []
        for product in products:
            product_dict = {}
            # try:
            # product_dict["image_url"] = product["images"][0]["src"]
            # except:
            # product_dict["image_url"] = None

            try:
                product_dict["product_name"] = product["name"]
            except:
                product_dict["product_name"] = "Unnamed product"

            product_dict["image_count"] = len(product["images"])

            product_dict["no_alts"] = 0
            for image in product["images"]:
                if not image["alt"]:
                    product_dict["no_alts"] += 1

            product_dict["description"] = product["description"]
            product_dict["description_word_count"] = len(
                product["description"].split(" ")
            )
            output["listings"].append(product_dict)

            output["stats"] = {}

            total_word_count = sum(
                product["description_word_count"] for product in output["listings"]
            )
            output["stats"]["average_word_count"] = round(
                total_word_count / len(products)
            )

            output["stats"]["no_alts"] = sum(
                product["no_alts"] for product in output["listings"]
            )

        return output

    def add_desc(self, product, overwrite: bool = False, max_length: int = 10000):
        log.info(f"Writing description for {product['name']}")
        output = {}

        if product["description"] and not overwrite:
            return {}

        else:
            image_url = product["images"][0]["src"]
            data = {
                "data": [
                    {
                        "question": Prompts.write_desc,
                        "image": image_url,
                        "languages": [self.language],
                        "features": ["question_answer"],
                        "output_length": max_length,
                    }
                ]
            }

            response = self.send_scenex_request(data)
            output["description"] = response["result"][0]["text"]
            output["id"] = product["id"]

            return output

    def add_alts(self, product, overwrite: bool = False):
        """
        All alt images for product featured image and gallery images

        Args:
            product: the product object

        Return:
            output: any fields that were updated
        """
        output = {}
        if product.get("name"):
            log.info(f"Processing {product['name']}")

        # product gallery images
        if product.get("images"):
            image_list = []
            counter = 0  # count how many images we've processed. If above zero, put data in output

            for i, image in enumerate(product["images"]):
                src = image["src"]

                log.info(f"Sending image {i+1}/{len(product['images'])} to SceneXplain")
                if overwrite:
                    image["alt"] = self.generate_alt_text(src)
                    counter += 1
                else:
                    if not image["alt"]:
                        image["alt"] = self.generate_alt_text(src)
                        counter += 1

                image_list.append(image)

            if counter > 0:
                output["images"] = image_list

            output["updated_alts_count"] = counter

        output["id"] = product.get("id")

        # body images
        # if product.get("description"):
        # html = product["description"]
        # product["description"] = HTMLHelper._process_html(HTMLHelper, html)

        return output

    def update_product(self, product: dict):
        """
        Update WooCommerce product.

        Args:
            product (dict): dict where keys are names of fields to update and values are data.

        Returns:
            updated_product (dict): Product dict with all populated fields
        """
        url_string = f"products/{product['id']}"
        updated_product = self.wcapi.put(url_string, product)

        return updated_product

    def update_products(self, products: list = []):
        if not products:
            products = self.get_products()

        for product in products:
            updated_product = self.add_alts(product)
            self.update_product(updated_product)

        log.info("All done")


class ShopifyHandler(AltTexter):
    def __init__(
        self,
        url: str,
        shopify_shop_name: str,
        shopify_access_token: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
    ):
        super().__init__(self, scenex_url=scenex_url, scenex_api_key=scenex_api_key)
        self.shopify_access_token = shopify_access_token
        self.shopify_url = (
            f"https://{shopify_shop_name}.myshopify.com/admin/api/2024-01/"
        )
        self.shopify_headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.shopify_access_token,
        }

    def get_products(self):
        url = self.shopify_url + "products.json"

        response = requests.get(url, headers=self.shopify_headers)
        if response.status_code == 200:
            products = response.json()["products"]

        return products

    def get_product(self, product_id):
        url = self.shopify_url + f"products/{product_id}.json"
        response = requests.get(url, headers=self.shopify_headers)
        product = None
        if response.status_code == 200:
            product = response.json()["product"]
        return product

    def add_alts(self, product):
        updated_data = {"id": product["id"]}
        log.info(f"Processing {product['title']}")
        counter = 0
        updated_images = []
        for image in product["images"]:
            if not image["alt"]:
                alt_text = self.generate_alt_text(image["src"])
                image["alt"] = alt_text
                updated_images.append(image)
                counter += 1

        if counter:
            updated_data["images"] = updated_images

        return updated_data

    def update_product(self, updated_data):
        url = self.shopify_url + f"products/{updated_data['id']}.json"
        payload = {"product": updated_data}
        log.info("Updating product")
        response = requests.put(
            url, headers=self.shopify_headers, data=json.dumps(payload)
        )
        if response.status_code == 200:
            print("Product updated successfully.")
            return response.json()["product"]
        else:
            print(
                f"Failed to update product. Status code: {response.status_code}, Response: {response.text}"
            )
            return None

    def update_products(self, products: list = []):
        if not products:
            products = self.get_products()

        for product in products:
            updated_data = self.add_alts(product)

            if "images" in updated_data:
                response = self.update_product(updated_data)
            else:
                log.info("Skipping product. Nothing to update")

        log.info("All done!")


class Debug:
    def url_to_datauri(image_url, file_path="./temp"):
        file_path = Debug.download_to_temp(image_url, file_path)
        datauri = Debug.image_to_data_uri(file_path)

        return datauri

    def image_to_data_uri(file_path):
        filename = file_path.split("/")[-1]
        log.info(f"Converting {filename} to datauri")

        with open(file_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded_image}"

    def download_to_temp(image_url, directory="./temp"):
        filename = image_url.split("/")[-1]
        log.info(f"Downloading {filename}")

        response = requests.get(image_url)
        response.raise_for_status()

        file_path = f"{directory}/{filename}"

        with open(file_path, "wb") as file:
            file.write(response.content)

        return file_path


class HTMLHelper(AltTexter):
    from difflib import unified_diff

    def __init__(self):
        super().__init__()

    def _process_html(self, html: str):
        """
        Find all images in HTML string, and add alt text if it doesn't exist.

        Args:
            html (str): HTML string
        """
        soup = BeautifulSoup(html, "html.parser")

        img_tags = soup.find_all("img")

        for img in img_tags:
            if not img["alt"]:
                img["alt"] = self.generate_alt_text(img["src"])
            else:
                log.info(f"{img['src']} already has alt text. Skipping")

        return str(soup)

    def _get_html_with_alt(self, doc):
        """
        Extract HTML and keep alt texts and overall structure (i.e. parameter ordering, etc). Helps run a meaningful diff on multiple HTML strings
        """
        html = tostring(doc, pretty_print=True).decode()
        for element in doc.iter():
            if "alt" in element.attrib:
                alt_text = f" [alt: {element.attrib['alt']}]"
                html = html.replace(
                    tostring(element, with_tail=False).decode(),
                    tostring(element, with_tail=False).decode() + alt_text,
                )
        return html

    def _is_html_changed(self, original_html, new_html) -> bool:
        """
        Check if HTML has been changed.

        Args:
            original_item (str): Original HTML.
            new_item (str): Updated HTML.

        Returns:
            True if original_item and new_item are different.
            False if original_item and new_item are the same.
        """
        original_doc = fromstring(original_html)
        new_doc = fromstring(new_html)

        original_html_with_alt = HTMLHelper._get_html_with_alt(self, original_doc)
        new_html_with_alt = HTMLHelper._get_html_with_alt(self, new_doc)

        console.print(original_html_with_alt)
        console.print(new_html_with_alt)

        diff_lines = list(
            unified_diff(
                original_html_with_alt.splitlines(),
                new_html_with_alt.splitlines(),
                lineterm="",
                fromfile="original",
                tofile="new",
            )
        )
        return len(diff_lines) > 0


class Prompts:
    write_desc = "Create an attractive and SEO friendly product description for use on an ecommerce website. It should make the product sound attractive and entice users to purchase it. Don't talk about the backdrop, only the product itself."
