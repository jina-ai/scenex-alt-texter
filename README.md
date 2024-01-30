# Alt Texter

This script automatically adds alt tags to all the images (including featured images) on your blog using [SceneXplain](https://scenex.jina.ai). Currently it supports [Ghost](https://ghost.org/), but other blogs/platforms can be added.

When you run the script or Docker image it will:

- Download each post from your blog
- Check each image to see if it has alt text:
    - If yes, skip that image
    - If no, create an alt text using SceneXplain and write that to the post data
- Check if the post has new alt texts:
    * If yes, update the post
    * If no, skip update

## You will need:

- A [SceneXplain](https://scenex.jina.ai) account and [API key](https://scenex.jina.ai/api).
- Your Ghost [**Admin** API](https://ghost.org/docs/admin-api/) key (not Content API key)

## What images/blogs does it support?

Currently the script supports Ghost blog posts:

- ✅ Featured images
- ✅ Inline images (basically normal images)
- ❌ Galleries (there seems to be no alt text field to even write)
- ❌ Thumbnails generated from bookmarks, YouTube video embeds, etc
- ❌ Ghost pages (not yet)

## Instructions

### Docker

Fill in the environment variables (denoted by angle brackets) and run the code.

```shell
docker run -d --name alt-texter \
-e GHOST_API_KEY=<ghost-api-key> \
-e SCENEX_API_KEY=<scenex-api-key> \
-e GHOST_BLOG_URL=<ghost-blog-url> \
jinaai/alt-texter:0.1
```

### Bare metal

1. Clone this repo then enter its directory.
2. Run `pip install -r requirements.txt` to install requirements.
2. Fill in the environment variables (denoted by angle brackets) and run the code.

```shell
env GHOST_API_KEY=<ghost-api-key> \
SCENEX_API_KEY=<scenex-api-key> \
GHOST_BLOG_URL="<ghost-blog-url>" \
python app.py
```
