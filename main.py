import json
import os

import requests
from dotenv import load_dotenv
from rich.console import Console

from helper import (add_alts, create_alt_text, get_ghost_token, get_post,
                    get_post_ids, is_post_changed, update_post)

load_dotenv()

console = Console(tab_size=2)
print = console.print

ghost_url = "https://jina-ai-gmbh.ghost.io/"

api_key = os.environ["GHOST_API_KEY"]
ghost_token = get_ghost_token(api_key)


def run_test():
    post_id = "65ae57f88da8040001e16ec5"

    original_post = get_post(post_id)
    updated_post_data = add_alts(post_id)

    if is_post_changed(original_post, updated_post_data):
        response = update_post(post_id, updated_post_data)

        print(response)
    else:
        print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")


run_test()

# post_ids = get_post_ids(status="draft")

# for post_id in post_ids:
# original_post = get_post(post_id)
# updated_post_data = add_alts(post_id)

# if is_post_changed(original_post, updated_post_data):
# response = update_post(post_id, updated_post_data)

# print(response)
# else:
# print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")
