import json
import logging
# import os
import time

import jwt
import requests
from rich.console import Console
from rich.logging import RichHandler

# if os.path.isfile(".env"):
# from dotenv import load_dotenv

console = Console(tab_size=2)

# set up logging
FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


class AltTexter:
    def __init__(self, url: str, scenex_api_key: str):
        # load_dotenv()
        # self.secrets = {"scenex_api_key": os.environ["SCENEX_API_KEY"]}
        # self.scenex_api_key = scenex_api_key

        # self.config = self.load_config("config.yml")

        self.scenex_headers = {
            "x-api-key": f"token {scenex_api_key}",
            "content-type": "application/json",
        }
        self.url = url

    # def load_config(self, config_file):
    # with open(config_file) as file:
    # config = yaml.safe_load(file)

    # return config

    def generate_alt_text(
        self, image_url: str, max_length: int = 125, max_tries: int = 3
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
        if image_url:
            filename = image_url.split("/")[-1]
            data = {
                "data": [
                    {"task_id": "alt_text", "languages": ["en"], "image": image_url}
                ]
            }

            # implement max tries since sometimes SX has issues
            alt_text = None
            alt_text_tries = 0

            while (not alt_text) and (alt_text_tries < max_tries):
                log.info(f"Sending {filename} to SceneXplain")
                response = requests.post(
                    self.scenex_url, headers=self.scenex_headers, json=data
                ).json()
                alt_text = response["result"][0]["text"][:max_length]

            return alt_text
        else:
            return None


class GhostTagger(AltTexter):
    def __init__(
        self, url: str, ghost_api_key: str, scenex_api_key: str, scenex_url: str
    ):
        super().__init__(url, scenex_api_key)
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

        log.info("Getting post IDs")
        response = requests.get(
            f"{self.ghost_url}/ghost/api/admin/posts/",
            headers=ghost_headers,
            params=params,
        )

        if response.status_code == 200:
            posts_data = response.json()
            post_ids = [post["id"] for post in posts_data["posts"]]
        else:
            log.error("Failed to retrieve posts")

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
            post_ids (list): list of post IDs to retrieve. If unset, retrieve 10,000 posts based on `order`.
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

    def update_all(self) -> None:
        """
        Create alt texts for all blog posts and write to Ghost.
        """
        post_ids = self._get_post_ids()
        for post_id in post_ids:
            original_post = self._get_post(post_id)
            updated_post = self.add_alts(post_id)
            if self._is_post_changed(original_post, updated_post):
                self.update_post(post_id=post_id, post_data=updated_post)
        log.info("All done!")


# class WooCommerceTagger(AltTexter):
# def __init__(self, url):
# super().__init__(url)

# def get_product_ids(self):
# # Your code to get product IDs
# pass

# def get_product(self):
# # Your code to get a single product
# pass

# def update_product(self):
# # Your code to update a product
# pass
