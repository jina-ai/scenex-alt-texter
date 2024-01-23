import json
import os
import time

import jwt
import requests
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from config import ghost_url, max_alt_length

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


ghost_token = get_ghost_token(ghost_api_key)
ghost_headers = {
    "Authorization": f"Ghost {ghost_token}",
    "Content-Type": "application/json",
}


def get_post_ids(status="published", limit=10_000, order="published_at desc"):
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
    headers = {"Authorization": f"Ghost {ghost_token}"}
    url = f"{ghost_url}/ghost/api/admin/posts/{post_id}"

    response = requests.get(url, headers=headers, params={"formats": "lexical"})
    if response.status_code == 200:
        post_data = response.json()
        post = post_data["posts"][0]
        return post
    else:
        print(response.json())
        return f"Error: {response.status_code}"


def create_alt_text(image_url, max_length=max_alt_length):
    filename = image_url.split("/")[-1]
    data = {"data": [{"task_id": "alt_text", "languages": ["en"], "image": image_url}]}

    scenex_headers = {
        "x-api-key": f"token {scenex_api_key}",
        "content-type": "application/json",
    }

    console.print(
        f"\t- Sending {filename} to [bright_magenta]SceneXplain[/bright_magenta]"
    )
    response = requests.post(
        "https://api.scenex.jina.ai/v1/describe", headers=scenex_headers, json=data
    ).json()
    # print(response)
    alt_text = response["result"][0]["text"][:max_length]

    return alt_text


def add_alts(post_id):
    post = get_post(post_id)
    print(f"- Processing [blue]{post['title']}[/blue]")

    # Process post featured image
    if not post["feature_image_alt"]:
        print("- Adding featured image alt text")
        post["feature_image_alt"] = create_alt_text(post["feature_image"])

    # Process post body

    # convert string to dict
    post["lexical"] = json.loads(post["lexical"])

    for row in post["lexical"]["root"]["children"]:
        if row["type"] == "image":
            if not row["alt"]:
                alt_text = create_alt_text(row["src"])
                row["alt"] = alt_text

    # convert dict back to string
    post["lexical"] = json.dumps(post["lexical"])

    return post


def is_post_changed(original_post, new_post):
    if (
        json.loads(original_post["lexical"]) != json.loads(new_post["lexical"])
        or original_post["feature_image_alt"] != new_post["feature_image_alt"]
    ):
        return True
    else:
        return False


def update_post(post_id, post_data):
    url = f"{ghost_url}ghost/api/admin/posts/{post_id}/"

    # keeps whining about jwt token expired, so let's recreate before we send the data
    ghost_headers = {
        "Authorization": f"Ghost {ghost_token}",
        "Content-Type": "application/json",
    }

    data = {"posts": [post_data]}

    console.print("\t- Sending updated post to [cyan]Ghost[/cyan]")
    response = requests.put(url, headers=ghost_headers, json=data)

    return response.json()
