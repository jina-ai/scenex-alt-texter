import time
from pprint import pprint

import jwt
import requests
from bs4 import BeautifulSoup

from config import ghost_api_key, ghost_url, scenex_api_key


def get_ghost_token(api_key=ghost_api_key):
    api_id, api_secret = api_key.split(":")

    payload = {"iat": int(time.time()), "exp": int(time.time()) + 300, "aud": "/admin/"}

    token = jwt.encode(
        payload, bytes.fromhex(api_secret), algorithm="HS256", headers={"kid": api_id}
    )
    print(token)

    return token


ghost_token = get_ghost_token(ghost_api_key)
ghost_headers = {
    "Authorization": f"Ghost {ghost_token}",
    "Content-Type": "application/json",
}


def get_post_ids(status="published", limit=10_000):
    params = {
        "filter": f"status:{status}",
        "limit": limit,
        "order": "published_at desc",
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
    params = {"formats": "html"}

    try:
        response = requests.get(
            f"{ghost_url}/ghost/api/admin/posts/{post_id}/",
            headers=ghost_headers,
            params=params,
        )

        if response.status_code == 200:
            return response.json()["posts"][0]
        else:
            return {"error": f"Failed to retrieve the post: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def add_alt_texts_to_html(post_id):
    # be explicit, otherwise it will try to add alts for stuff like repo preview cards, svgs, etc
    image_formats = ["jpg", "jpeg", "png", "gif"]

    post = get_post(post_id)
    html = post["html"]
    soup = BeautifulSoup(html)

    for img_tag in soup.find_all("img"):
        url = img_tag["src"]
        if url.split(".")[-1].lower() in image_formats:
            alt_text = create_alt_text(img_tag["src"])
            if not img_tag.get("alt"):
                img_tag["alt"] = alt_text

    return str(soup)


def create_alt_text(image_url):
    print(f"- Processing {image_url}")
    data = {"data": [{"task_id": "alt_text", "languages": ["en"], "image": image_url}]}

    scenex_headers = {
        "x-api-key": f"token {scenex_api_key}",
        "content-type": "application/json",
    }

    response = requests.post(
        "https://api.scenex.jina.ai/v1/describe", headers=scenex_headers, json=data
    ).json()
    pprint(response)
    alt_text = response["result"][0]["text"]

    return alt_text
