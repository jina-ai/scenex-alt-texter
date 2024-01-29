# Auto Alt Tagger

This script automatically adds alt tags to all the images (including featured images) on your blog using [SceneXplain](https://scenex.jina.ai). Currently it supports Ghost, but other blogs/platforms can be added.

## Instructions

First of all, clone this repo then enter its directory. Then:

### Docker

You'll need to set your environment variables in the Docker command then run it:

```
docker build -t alt-texter .
docker run -d --name myapp-container -e GHOST_API_KEY=your_ghost_api_key -e GHOST_BLOG_URL=your_ghost_blog_url -e SCENEX_URL=your_scenex_url myapp
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

4. `pip install -r requirements.txt`
6. Run `python app.py`
