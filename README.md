# Auto Alt Tagger

This script automatically adds alt tags to all the images (including featured images) on your blog using [SceneXplain](https://scenex.jina.ai). Currently it supports Ghost, but other blogs/platforms can be added.

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
- Your Ghost **Admin** API key (not Content API key)

## What images/blogs does it support?

Currently the script supports Ghost blogs:

- ✅ Featured images
- ✅ Inline images (basically normal images)
- ❌ Galleries (there seems to be no alt text field to even write)
- ❌ Thumbnails generated from bookmarks, YouTube video embeds, etc

## Instructions

First of all, clone this repo then enter its directory. Then:

### Docker

You'll need to set your environment variables in the Docker command then run it:

```
docker build -t alt-texter .
docker run -d --name alt-texter-container -e GHOST_API_KEY=your_ghost_admin_api_key -e GHOST_BLOG_URL=your_ghost_blog_url -e SCENEX_URL=your_scenex_url alt-texter
```

### Bare metal

#### Get API keys

1. Sign up for an account on [SceneXplain](https://scenex.jina.ai) and create an [API key](https://scenex.jina.ai/api)
2. Get your Ghost Admin API key

#### Set environment variables

You'll need to set:
- `SCENEX_API_KEY`
- `GHOST_API_KEY`
- `GHOST_BLOG_URL`

#### Run the script

1. `pip install -r requirements.txt`
2. Run `python app.py`

## TODO

### In progress

- WordPress support

### Future

- WooCommerce support
- Ghost pages support
