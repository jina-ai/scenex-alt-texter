import os

from dotenv import load_dotenv

load_dotenv()

ghost_url = "https://jina-ai-gmbh.ghost.io/"
ghost_api_key = os.environ["GHOST_API_KEY"]
scenex_api_key = os.environ["SCENEX_API_KEY"]
image_formats = ["jpg", "jpeg", "png", "gif"]

max_alt_length = 124
