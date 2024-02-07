# Alt Texter

This script automatically adds alt tags to all the images (including featured images) on your blog using [SceneXplain](https://scenex.jina.ai). 

## What platforms does it support?

| Platform | Post images | Page images | Media images | Product images | Notes |
| --- | --- | --- | --- | --- | --- |
| Ghost | ✅ | Pending | N/A | N/A | Tested, works decently |
| WordPress | ✅ | ✅ | ✅ | N/A | Converts post content to HTML |
| WooCommerce | Use WordPress handler | Use WordPress handler | Use Wordpress handler | ✅ | Experimental |
| Shopify | ✅ | | | ✅ | Experimental |

## How does it work?

When you run the script or Docker image it will:

- Download each content item from whatever platform you're using
- Check each image to see if it has alt text:
    - If yes, skip that image
    - If no, create an alt text using SceneXplain and write that to the post data
- Check if the content has new alt texts:
    * If yes, update the content
    * If no, skip update

## Instructions

### Set API environment variables

Environment variables let you safely define your credentials and settings. No matter which platform you use, you will need:

| Environment variable name | Required? | Default value | Notes |
| --- | --- | --- | --- | 
| `PLATFORM` | No | `ghost` | `ghost`, `wordpress`, `woocommerce` or `shopify` |
| `SCENEX_API_KEY` | Yes | None | Generate [here](https://scenex.jina.ai/api) |

Then, depending on your platform, you will need to set additional variables to define your URL and credientials:

#### Ghost

| Environment variable name | Required? | Default value | Notes |
| --- | --- | --- | --- | 
| `GHOST_BLOG_URL` | Yes | None | Must include "http(s)" prefix |
| `GHOST_API_KEY` | Yes | None | |

#### WordPress

| Environment variable name | Required? | Default value | Notes |
| --- | --- | --- | --- | 
| `WORDPRESS_URL` | Yes | None | Must include "http(s)" prefix |
| `WORDPRESS_USERNAME` | Yes | None | |
| `WORDPRESS_PASSWORD` | Yes | None | |

#### WooCommerce

| Environment variable name | Required? | Default value | Notes |
| --- | --- | --- | --- | 
| `WOOCOMMERCE_URL` | Yes | None | Must include "http(s)" prefix |
| `WOOCOMMERCE_KEY` | Yes | None | Your WooCommerce consumer key |
| `WOOCOMMERCE_SECRET` | Yes | None | Your WooCommerce consumer secret |

#### Shopify

| Environment variable name | Required? | Default value | Notes |
| --- | --- | --- | --- | 
| `SHOPIFY_SHOP_NAME` | Yes | None | |
| `SHOPIFY_ACCESS_TOKEN` | Yes | None | Your Shopify [Admin API](https://shopify.dev/api/admin) access token |

### Run in Docker

Fill in the environment variables (denoted by angle brackets) and run the code. For each line that begins with `-e` you'll need to specify each of your environment variables from your platform above. For example, if you use Ghost, you would specify:

```shell
docker run -d --name alt-texter \
-e SCENEX_API_KEY=<scenex-api-key> \
-e PLATFORM=ghost \
-e GHOST_API_KEY=<ghost-api-key> \
-e GHOST_BLOG_URL="<ghost-blog-url>" \
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

## FAQ

### Why doesn't the WooCommerce handler update my posts and pages?

WooCommerce is a WordPress plugin, so you should use the WordPress handler to update the posts and pages on your site.

### Do you plan any proper plugins for the platforms?

I have no expertise in that area. If someone wants to lend a hand, drop an issue and let's chat!
