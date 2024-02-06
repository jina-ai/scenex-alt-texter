import os

from helper import GhostTagger

GHOST_API_KEY = os.environ["GHOST_API_KEY"]
GHOST_BLOG_URL = os.environ["GHOST_BLOG_URL"]
SCENEX_API_KEY = os.environ["SCENEX_API_KEY"]
SCENEX_URL = "https://api.scenex.jina.ai/v1/describe"

# post_ids = ["641c2fcdf4d50d003d590477"]

if __name__ == "__main__":
    alt_texter = GhostTagger(
        url=GHOST_BLOG_URL,
        ghost_api_key=GHOST_API_KEY,
        scenex_api_key=SCENEX_API_KEY,
        scenex_url=SCENEX_URL,
    )

    alt_texter.update_all()
