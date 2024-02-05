import base64
import json
import logging
import tempfile
# import os
import time
from difflib import unified_diff

import jwt
import requests
from bs4 import BeautifulSoup
from lxml.html import diff, fromstring, tostring
from requests.auth import HTTPBasicAuth
from rich.console import Console
from rich.logging import RichHandler
from woocommerce import API

console = Console(tab_size=2)

# set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")

SCENEX_URL = "https://api.scenex.jina.ai/v1/describe"


class AltTexter:
    def __init__(self, url: str, scenex_api_key: str, scenex_url: str = SCENEX_URL):
        self.scenex_headers = {
            "x-api-key": f"token {scenex_api_key}",
            "content-type": "application/json",
        }
        self.url = url
        self.scenex_url = scenex_url

    def generate_alt_text(
        self,
        image_url: str,
        max_length: int = 125,
        max_tries: int = 3,
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
        if self._validate_image(image_url):
            print(image_url)
            filename = image_url.split("/")[-1]
            data = {"data": [{"task_id": "alt_text", "image": image_url}]}

            # implement max tries since sometimes SX has issues
            alt_text = None
            alt_text_tries = 0

            while (not alt_text) and (alt_text_tries < max_tries):
                log.info(f"Sending {filename} to SceneXplain")
                response = requests.post(
                    url=self.scenex_url, headers=self.scenex_headers, json=data
                )
                alt_text = response.json()["result"][0]["text"][:max_length]

            return alt_text
        else:
            return

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


class GhostTagger(AltTexter):
    def __init__(
        self,
        url: str,
        ghost_api_key: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
    ):
        super().__init__(url, scenex_api_key, scenex_url)
        self.ghost_api_key = ghost_api_key
        self.ghost_url = url
        self.scenex_url = scenex_url

    def _get_ghost_token(self, ghost_api_key: str):
        """
        Get a Ghost token from API key

        Args:
            ghost_api_key (str): Your Ghost Admin API key.

        Returns:
            token: Resulting Ghost token.
        """
        api_id, api_secret = ghost_api_key.split(":")

        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 300,
            "aud": "/admin/",
        }

        token = jwt.encode(
            payload,
            bytes.fromhex(api_secret),
            algorithm="HS256",
            headers={"kid": api_id},
        )

        return token

    def _renew_headers(self, ghost_api_key: str) -> dict:
        """
        Ghost tokens expire after a while. This function recreates the token and returns updated headers.

        Args:
            ghost_api_key (str): Your Ghost Admin API key.

        Returns:
            ghost_headers (dict): Updated Ghost headers.
        """
        ghost_headers = {
            "Authorization": f"Ghost {self._get_ghost_token(ghost_api_key)}",
            "Content-Type": "application/json",
        }

        return ghost_headers

    def _get_post_ids(
        self,
        status: str = "published",
        limit: int = 10_000,
        order: str = "published_at desc",
    ) -> list:
        """
        Get IDs of all posts in Ghost blog.

        Args:
            status (str): published/scheduled/draft.
            limit (int): maximum number of post ids to retrieve.
            order (str): ordering method to use, followed by 'asc' (ascending) or 'desc' (descending).

        Returns:
            post_ids (list): a list of strings, where each string is a separate post.id.
        """
        ghost_headers = self._renew_headers(self.ghost_api_key)

        params = {
            "filter": f"status:{status}",
            "limit": limit,
            "order": order,
            "fields": "id",
        }

        response = requests.get(
            f"{self.ghost_url}/ghost/api/admin/posts/",
            headers=ghost_headers,
            params=params,
        )

        log.info("Getting Ghost post IDs")
        if response.status_code == 200:
            posts_data = response.json()
            post_ids = [post["id"] for post in posts_data["posts"]]
        else:
            log.error(f"Failed to retrieve posts: {response.text}")

        return post_ids

    def _get_post(self, post_id: str) -> dict:
        """
        Get an individual Ghost blog post.

        Args:
            post_id (str): Post ID of the post you wish to retrieve.

        Returns:
            post (dict): The post with the post ID you requested.
        """
        url = f"{self.ghost_url}/ghost/api/admin/posts/{post_id}"

        ghost_headers = self._renew_headers(self.ghost_api_key)
        response = requests.get(
            url, headers=ghost_headers, params={"formats": "lexical"}
        )

        if response.status_code == 200:
            post_data = response.json()
            post = post_data["posts"][0]
            return post
        else:
            log.error(f"Failed to retrieve post with ID {post_id}")
            return response.json()
            # return f"Error: {response.status_code}"

    def _get_posts(
        self,
        post_ids=[],
        status: str = "published",
        limit: int = 10_000,
        order: str = "published_at desc",
    ) -> list:
        """
        Get all posts in Ghost blog.

        Args:
            post_ids (list): list of post IDs to retrieve. If unset, retrieve 10,000.
            status (str): published/scheduled/draft.
            limit (int): maximum number of post ids to retrieve.
            order (str): ordering method to use, followed by 'asc' (ascending) or 'desc' (descending).

        Returns:
            post_ids (list): a list of strings, where each string is a separate post.id.
        """
        if not post_ids:
            post_ids = self._get_post_ids(status, limit, order)

        posts = [self._get_post(post_id) for post_id in post_ids]

        return posts

    def update_post(self, post_id, post_data) -> dict:
        """
        Update an individual Ghost blog post.

        Args:
            post_id (str): Post ID of the post you wish to update.
            post_data (dict): The updated post content you wish to write.

        Returns:
            response.json(): The updated post
        """
        url = f"{self.ghost_url}ghost/api/admin/posts/{post_id}/"
        data = {"posts": [post_data]}

        ghost_headers = self._renew_headers(self.ghost_api_key)
        log.info("Sending updated post to Ghost")
        response = requests.put(url, headers=ghost_headers, json=data)

        return response.json()

    def add_alts(self, post_id, max_tries=3) -> dict:
        """
        Add alt texts for all images in an individual Ghost post.

        Args:
            post_id (str): Post ID of the post you wish to add alts for.
            max_tries (int): How many times to try generating an alt text before giving up.

        Returns:
            post (dict): post (based on post_id arg) updated with alt texts.
        """
        post = self._get_post(post_id)
        log.info(f"Processing {post['title']}")

        # Process featured image
        if not post["feature_image_alt"]:
            alt_text = self.generate_alt_text(post["feature_image"])
            if alt_text:
                post["feature_image_alt"] = alt_text[:125]  # Ghost has hard limit here

        # Process post body
        if post["lexical"]:
            post["lexical"] = json.loads(post["lexical"])
            self.add_alt_text_recursive(post["lexical"]["root"]["children"])
            post["lexical"] = json.dumps(post["lexical"])

        return post

    def add_alt_text_recursive(self, rows) -> None:
        """
        Recurse through all nested structures in an individual Ghost blog post and add alt texts.
        """
        for row in rows:
            if row.get("type") == "image":
                if "alt" not in row:  # older posts don't even have the alt field
                    row["alt"] = None
                if not row["alt"]:
                    alt_text = self.generate_alt_text(row["src"])
                    row["alt"] = alt_text

            # Recursively process nested rows
            if "children" in row and isinstance(row["children"], list):
                self.add_alt_text_recursive(row["children"])

    def _is_post_changed(self, original_post, new_post) -> bool:
        """
        Check if post content has been updated. Checks post content and featured image.

        Args:
            original_post (dict): Original Ghost blog post.
            new_post (dict): Updated version of Ghost blog post, relative to original.

        Returns:
            True if original_post and new_post are different.
            False if original_post and new_post are the same.
        """
        if new_post["lexical"]:
            if json.loads(original_post["lexical"]) != json.loads(new_post["lexical"]):
                return True

        if new_post["feature_image_alt"]:
            if original_post["feature_image_alt"] != new_post["feature_image_alt"]:
                return True

        return False

    def update_all(self, post_ids: list = []) -> None:
        """
        Create alt texts for all blog posts and write to Ghost.
        """
        if not post_ids:
            post_ids = self._get_post_ids()

        for post_id in post_ids:
            original_post = self._get_post(post_id)
            updated_post = self.add_alts(post_id)
            if self._is_post_changed(original_post, updated_post):
                self.update_post(post_id=post_id, post_data=updated_post)
        log.info("All done!")


class WordPressTagger(AltTexter):
    def __init__(
        self,
        wordpress_url: str,
        wordpress_username: str,
        wordpress_password: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
    ):
        super().__init__(wordpress_url, scenex_api_key, scenex_url)
        self.full_url = f"{self.url}/wp-json/wp/v2/"
        self.scenex_url = scenex_url
        self.wordpress_username = wordpress_username
        self.wordpress_password = wordpress_password
        self.basic_types = ["post", "page"]  # basic content types, e.g. page, product

    def _get_items(
        self, content_types: str = ["posts"], limit: int = 100, status: str = "publish"
    ) -> list:
        """
        Get posts or pages
        """
        items_per_page = 100
        all_items = []
        for content_type in content_types:
            url = f"{self.url}/wp-json/wp/v2/{content_type}"

            page = 1
            log.info(f"Getting WordPress {content_type}")
            while len(all_items) < limit:
                params = {
                    "per_page": items_per_page,
                    "page": page,
                }

                if content_type != "media":
                    params["status"] = status

                response = requests.get(url, params=params)
                if response.status_code == 200:
                    items = response.json()
                    if not items:
                        break  # No more posts available
                    all_items.extend(items)
                    if len(items) < items_per_page:
                        break  # This is the last page of items
                    page += 1
                else:
                    log.error(
                        f"Failed to retrieve WordPress {content_type}, Status Code: {response.status_code}"
                    )
                    break

        return all_items[:limit]

    def get_item(self, item_type: str, item_id: str):
        """
        Get a WordPress content object.

        Args:
            item_type (str): typically 'pages', 'posts', or 'media'.
            item_id (str): object id.
        """
        item_url = f"{self.full_url}{item_type}/{item_id}"
        response = requests.get(
            item_url,
            auth=HTTPBasicAuth(self.wordpress_username, self.wordpress_password),
        )
        if response.status_code == 200:
            item = response.json()
            return item
        else:
            logging.warn(
                f"Failed to retrieve {item_type} with ID {item_id}, Status Code: {response.status_code}"
            )

    def add_alts(self, content_object):
        """
        Add alt texts for content item.

        Args:
            content_object: WordPress object, like post, page, media
        """
        log.info(f"Processing {content_object['title']['rendered']}")
        updated_object = {"id": content_object["id"], "type": content_object["type"]}

        if content_object["type"] in self.basic_types:
            html = content_object["content"]["rendered"]

            new_html = HTMLHelper._process_html(self, html=html)
            # content_object["content"]["rendered"] = new_html
            updated_object["content"] = new_html.strip()

        elif content_object["type"] == "attachment":
            media_url = content_object["source_url"]
            # media_url = "https://cdn.vox-cdn.com/thumbor/xYSUaNbrtoz-HUrW5CIStGurgWk=/0x0:4987x3740/1200x800/filters:focal(0x0:4987x3740)/cdn.vox-cdn.com/uploads/chorus_image/image/45503430/453801468.0.0.jpg"
            updated_object["alt_text"] = self.generate_alt_text(media_url)
            # updated_object = self.add_media_alt(content_object)

        return updated_object

    # def add_media_alt(self, content_object):
    # """
    # Add alt text for featured images

    # Args:
    # content_object: WordPress object, like post, page, media
    # """
    # media_url = content_object["source_url"]
    # if not content_object.get("alt_text"):
    # log.info(f"No alt text for media with ID {content_object['id']}")

    # # temporary testing url

    # content_object["alt_text"] = self.generate_alt_text(media_url)
    # else:
    # log.info(f"{media_url} already has alt text. Skipping")

    # return content_object

    def update_item(self, content_object):
        """
        Send updated content to WordPress API

        Args:
            - content_object (dict): dict of the content object to update
        """
        # console.print(content_object)

        content_id = content_object["id"]
        content_type = content_object["type"]

        if content_type in self.basic_types:
            content_string = content_type + "s"
            new_content = {"content": content_object["content"]}
        elif content_type == "attachment":
            pass
            new_content = {"alt_text": content_object["alt_text"]}
            content_string = "media"

        url = f"{self.full_url}{content_string}/{content_id}"

        # content_json = json.dumps(new_content)
        # content_json = {"content": content_object["content"]}

        log.info(f"Updating content item {content_id}")

        update_response = requests.post(
            url,
            auth=HTTPBasicAuth(self.wordpress_username, self.wordpress_password),
            json=new_content,
        )

        return update_response

    def _is_item_changed(self, original_item, new_item):
        original_html = str(original_item["content"]["rendered"])
        new_html = str(new_item["content"]["rendered"])

        html_changed = HTMLHelper._is_html_changed(self, original_html, new_html)

        # still need to compare featured image alt

        return html_changed


class HTMLHelper(AltTexter):
    from difflib import unified_diff

    from lxml.html import fromstring, tostring

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


class WooCommerceTagger(AltTexter):
    def __init__(
        self,
        url: str,
        woocommerce_consumer_key: str,
        woocommerce_consumer_secret: str,
        scenex_api_key: str,
        scenex_url: str = SCENEX_URL,
    ):
        self.wcapi = API(
            url=url,
            consumer_key=woocommerce_consumer_key,
            consumer_secret=woocommerce_consumer_secret,
            version="wc/v3",
        )
        super().__init__(self, scenex_url, scenex_api_key)

    def get_products(self):
        """
        Get list of all WooCommerce products.
        """
        log.info("Getting WooCommerce products")
        products = self.wcapi.get("products").json()

        return products

    def add_alts(self, product):
        """
        All alt images for product featured image and gallery images

        Args:
            product: the product object
        """
        if product.get("name"):
            log.info(f"Processing {product['name']}")

        # product gallery images
        if product.get("images"):
            for image in product["images"]:
                src = image["src"]

                if not image["alt"]:
                    image["alt"] = self.generate_alt_text(src)

        # body images
        if product.get("description"):
            html = product["description"]
            product["description"] = HTMLHelper._process_html(html)

        return product


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
