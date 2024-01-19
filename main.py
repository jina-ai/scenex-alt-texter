from helper import add_alt_texts_to_html, get_post, get_post_ids

post_ids = get_post_ids(limit=1)

posts = []
for post_id in post_ids:
    post = get_post(post_id)
    print(post["title"])
    posts.append(post)

test_post_html = add_alt_texts_to_html(post_ids[0])

print(test_post_html)
