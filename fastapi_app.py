import asyncio
import json
import os
import time

import jwt
import requests
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from rich.console import Console

from helper import get_ghost_token, get_post_ids

# load config
with open("config.yml") as file:
    config = yaml.safe_load(file)

max_alt_length = config["max_alt_length"]
ghost_url = config["ghost_url"]
scenex_url = config["scenex_url"]

# load secrets
load_dotenv()
ghost_api_key = os.environ["GHOST_API_KEY"]
scenex_api_key = os.environ["SCENEX_API_KEY"]

console = Console(tab_size=2)
print = console.print

app = FastAPI()


ghost_token = get_ghost_token()
ghost_headers = {
    "Authorization": f"Ghost {ghost_token}",
    "Content-Type": "application/json",
}


async def generate_posts(
    status: str = Query(default="published", description="Post status"),
    limit: int = Query(default=10, description="Number of posts to retrieve"),
    order: str = Query(default="published_at desc", description="Order to sort"),
):
    ghost_headers["Authorization"] = f"Ghost {get_ghost_token()}"

    post_ids = get_post_ids(status, limit, order)

    for post_id in post_ids:
        post = get_post(post_id)
        yield json.dumps(post) + "\n"

    # posts = [get_post(post_id) for post_id in post_ids]

    # return posts


@app.get("/posts")
def stream_posts(
    status: str = Query(default="published", description="Post status"),
    limit: int = Query(default=10, description="Number of posts to retrieve"),
    order: str = Query(default="published_at desc", description="Order to sort"),
):
    return StreamingResponse(
        generate_posts(status, limit, order), media_type="application/json"
    )


def get_post(post_id):
    url = f"{ghost_url}/ghost/api/admin/posts/{post_id}"

    # update token
    ghost_headers["Authorization"] = f"Ghost {get_ghost_token()}"

    response = requests.get(url, headers=ghost_headers, params={"formats": "lexical"})
    if response.status_code == 200:
        post_data = response.json()
        post = post_data["posts"][0]
        return post
    else:
        print(response.json())
        return f"Error: {response.status_code}"


def create_alt_text(
    image_url: str,
    max_length: int = Query(
        default=max_alt_length, description="Maximum length of alt text"
    ),
    max_tries: int = Query(
        default=3, description="Maximum attempts to create an alt text per image"
    ),
):
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
    ghost_headers["Authorization"] = f"Ghost {get_ghost_token()}"
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


def post_to_json(post_id):
    post = get_post(post_id)
    lexical = json.loads(post["lexical"])

    with open(f"{post['title']}.json", "w") as file:
        file.write(json.dumps(lexical))


def add_alts_orig(
    post_id: str,
    max_tries: int = Query(default=3, description="Maximum tries to create alt image"),
):
    post = get_post(post_id)
    print(f"- Processing [blue]{post['title']}[/blue]")

    # Process featured image
    if not post["feature_image_alt"]:
        alt_text = create_alt_text(post["feature_image"])
        if alt_text:
            post["feature_image_alt"] = alt_text[:125]  # Ghost has hard limit here

    # Process post body
    if post["lexical"]:
        post["lexical"] = json.loads(post["lexical"])
        add_alt_text_recursive(post["lexical"]["root"]["children"])
        post["lexical"] = json.dumps(post["lexical"])

    return post


@app.get("/{post_id}/add_alts")
async def add_alts(
    post_id: str,
    max_tries: int = Query(default=3, description="Maximum tries to create alt image"),
):
    yield json.dumps({"id": 1, "message": "Getting post"})
    post = get_post(post_id)
    await asyncio.sleep(1)
    yield json.dumps({"id": 2, "message": f"Processing {post['title']}"})

    # Process featured image
    if not post["feature_image_alt"]:
        alt_text = create_alt_text(post["feature_image"])
        if alt_text:
            post["feature_image_alt"] = alt_text[:125]  # Ghost has hard limit here

    # Process post body
    if post["lexical"]:
        post["lexical"] = json.loads(post["lexical"])
        add_alt_text_recursive(post["lexical"]["root"]["children"])
        post["lexical"] = json.dumps(post["lexical"])

    # return post


def add_alt_text_recursive(rows):
    for row in rows:
        if row.get("type") == "image":
            if "alt" not in row:  # older posts don't even have the alt field
                row["alt"] = None
            if not row["alt"]:
                alt_text = create_alt_text(row["src"])
                row["alt"] = alt_text

        # Recursively process nested rows
        if "children" in row and isinstance(row["children"], list):
            add_alt_text_recursive(row["children"])
