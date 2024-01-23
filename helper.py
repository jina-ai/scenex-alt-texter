import json
import time

import jwt
import requests
from rich.console import Console

from config import (ghost_api_key, ghost_url, image_formats, max_alt_length,
                    scenex_api_key)

console = Console(tab_size=2)
print = console.print


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
    # ghost_token = get_ghost_token(api_key)
    ghost_headers = {
        "Authorization": f"Ghost {ghost_token}",
        "Content-Type": "application/json",
    }

    # check if post has been updated with new data. skip if not
    # original_post = get_post(post_id)
    # if check_post_changed(original_post, post_data):
    data = {"posts": [post_data]}

    console.print("\t- Sending updated post to [cyan]Ghost[/cyan]")
    response = requests.put(url, headers=ghost_headers, json=data)

    return response.json()


# def get_post(post_id):
# params = {"formats": "html"}

# try:
# response = requests.get(
# f"{ghost_url}/ghost/api/admin/posts/{post_id}/",
# headers=ghost_headers,
# params=params,
# )

# if response.status_code == 200:
# return response.json()["posts"][0]
# else:
# return {"error": f"Failed to retrieve the post: {response.text}"}
# except Exception as e:
# return {"error": str(e)}


# def add_alt_texts_to_html(post_id, max_length=max_alt_length):
# """
# - Iterate through post's image tags and add alt text for images that lack it.
# - Skip certain images that are often GitHub cards, etc
# - If alt tags have been added, return the updated HTML
# - Otherwise return None
# """
# new_alts = 0  # counter for new alt texts. If > 1, send data
# # be explicit, otherwise it will try to add alts for stuff like repo preview cards, svgs, etc

# post = get_post(post_id)
# html = post["html"]
# soup = BeautifulSoup(html, "html.parser")

# for img_tag in soup.find_all("img"):
# url = img_tag["src"]
# if url.split(".")[-1].lower() in image_formats:
# if not img_tag.get("alt"):
# alt_text = create_alt_text(img_tag["src"])
# img_tag["alt"] = alt_text
# new_alts += 1

# if new_alts > 0:
# return str(soup)
# else:
# return None


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


# def update_post(post_id, data={}):
# url = f"{ghost_url}ghost/api/admin/posts/{post_id}/"
# post = get_post(post_id)
# console.print(f"- Processing [blue]{post['title']}[/blue]")
# console.print(post)

# # Create alt text for featured image
# if post["feature_image"]:
# if not post["feature_image_alt"]:
# feature_image_alt = create_alt_text([post["feature_image"]])
# data["feature_image_alt"] = feature_image_alt

# # Create alt text for all images. If nothing to update, return None
# html = add_alt_texts_to_html(post_id)

# # only add html field if alt tags have been added
# # if html:
# data["html"] = html
# # mobiledoc = html_to_mobiledoc(html)
# # data["mobiledoc"] = mobiledoc

# # Check we actually have any data to send
# # if len(data.keys()) > 0:
# data["updated_at"] = post["updated_at"]
# data = {"posts": [data]}

# # keeps whining about jwt token expired, so let's recreate before we send the data
# ghost_token = get_ghost_token(ghost_api_key)
# ghost_headers = {
# "Authorization": f"Ghost {ghost_token}",
# "Content-Type": "application/json",
# }

# # Check data

# console.print("\t- Sending data to [cyan]Ghost[/cyan]")
# response = requests.put(url, headers=ghost_headers, json=data)

# return response
# # else:
# # console.print("\tNothing to update")
