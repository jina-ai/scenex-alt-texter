import json
import os
import time

import jwt
import requests
import yaml
from dotenv import load_dotenv
from rich.console import Console

# from config import ghost_url, max_alt_length, scenex_url

load_dotenv()

with open("config.yml") as file:
    config = yaml.safe_load(file)


console = Console(tab_size=2)
print = console.print

ghost_api_key = os.environ["GHOST_API_KEY"]
scenex_api_key = os.environ["SCENEX_API_KEY"]


def get_ghost_token(api_key=ghost_api_key):
    api_id, api_secret = api_key.split(":")

    payload = {"iat": int(time.time()), "exp": int(time.time()) + 300, "aud": "/admin/"}

    token = jwt.encode(
        payload, bytes.fromhex(api_secret), algorithm="HS256", headers={"kid": api_id}
    )

    return token


ghost_token = get_ghost_token()
ghost_headers = {
    "Authorization": f"Ghost {ghost_token}",
    "Content-Type": "application/json",
}


def get_post_ids(status="published", limit=10_000, order="published_at desc"):
    # update token
    ghost_headers["Authorization"] = f"Ghost {get_ghost_token()}"

    params = {
        "filter": f"status:{status}",
        "limit": limit,
        "order": order,
    }

    response = requests.get(
        f"{ghost_url}/ghost/api/admin/posts/", headers=ghost_headers, params=params
    )

    if response.status_code == 200:
        posts_data = response.json()
        post_ids = [post["id"] for post in posts_data["posts"]]
    else:
        print(f"Failed to retrieve posts: {response.text}")

    return post_ids


def get_post(post_id):
    url = f"{ghost_url}/ghost/api/admin/posts/{post_id}"

    # update token
    ghost_headers["Authorization"] = f"Ghost {get_ghost_token()}"

    # token = get_ghost_token()
    # headers = {
    # "Authorization": f"Ghost {token}",
    # "Content-Type": "application/json",
    # }
    response = requests.get(url, headers=ghost_headers, params={"formats": "lexical"})
    if response.status_code == 200:
        post_data = response.json()
        post = post_data["posts"][0]
        return post
    else:
        print(response.json())
        return f"Error: {response.status_code}"


def create_alt_text(image_url, max_length=max_alt_length, max_tries=3):
    # sometimes image_url is None, so we need to handle that
    if image_url:
        filename = image_url.split("/")[-1]
        data = {
            "data": [{"task_id": "alt_text", "languages": ["en"], "image": image_url}]
        }

        scenex_headers = {
            "x-api-key": f"token {scenex_api_key}",
            "content-type": "application/json",
        }

        # implement max tries since sometimes SX has issues
        alt_text = None
        alt_text_tries = 0

        while (not alt_text) and (alt_text_tries < max_tries):
            console.print(
                f"\t- Sending {filename} to [bright_magenta]SceneXplain[/bright_magenta]"
            )
            response = requests.post(
                scenex_url, headers=scenex_headers, json=data
            ).json()
            # print(response)
            alt_text = response["result"][0]["text"][:max_length]

        return alt_text
    else:
        return None


def add_alts(post_id, max_tries=3):
    post = get_post(post_id)
    print(f"- Processing [blue]{post['title']}[/blue]")

    # Process featured image
    if not post["feature_image_alt"]:
        alt_text = create_alt_text(post["feature_image"])

        if alt_text:
            post["feature_image_alt"] = alt_text[:125]  # Ghost has hard limit here

    # Process post body
    # convert string to dict if lexical data exists. Otherwise don't touch it
    if post["lexical"]:
        post["lexical"] = json.loads(post["lexical"])

        for row in post["lexical"]["root"]["children"]:
            if row["type"] == "image":
                if "alt" not in row:  # older posts don't even have the alt field
                    row["alt"] = None

                if not row["alt"]:
                    alt_text = create_alt_text(row["src"])
                    row["alt"] = alt_text

        # convert dict back to string
        post["lexical"] = json.dumps(post["lexical"])

    return post


def is_post_changed(original_post, new_post):
    if new_post["lexical"]:
        if json.loads(original_post["lexical"]) != json.loads(new_post["lexical"]):
            return True

    if new_post["feature_image_alt"]:
        if original_post["feature_image_alt"] != new_post["feature_image_alt"]:
            return True

    return False


def update_post(post_id, post_data):
    url = f"{ghost_url}ghost/api/admin/posts/{post_id}/"
    data = {"posts": [post_data]}

    # keeps whining about jwt token expired, so let's recreate before we send the data
    token = get_ghost_token()
    ghost_headers = {
        "Authorization": f"Ghost {token}",
        "Content-Type": "application/json",
    }
    console.print("\t- Sending updated post to [cyan]Ghost[/cyan]")
    response = requests.put(url, headers=ghost_headers, json=data)

    return response.json()


def run_test():
    # get dummy post
    post_id = "65ae57f88da8040001e16ec5"

    original_post = get_post(post_id)
    updated_post_data = add_alts(post_id)

    if is_post_changed(original_post, updated_post_data):
        response = update_post(post_id, updated_post_data)

        print(response)
    else:
        print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")
