from rich.console import Console

from helper import (add_alts, get_post, get_post_ids, is_post_changed,
                    update_post)

console = Console(tab_size=2)
print = console.print

post_ids = get_post_ids(status="published")
updated_posts = []

for post_id in post_ids:
    original_post = get_post(post_id)
    updated_post_data = add_alts(post_id)
    if is_post_changed(original_post, updated_post_data):
        response = update_post(post_id, updated_post_data)
        updated_posts.append(updated_post_data)
    else:
        print("\t- No change needed")

# Print summary
if updated_posts:
    print("\nUpdated posts")
    for post in updated_posts:
        print(f'\t- {post["title"]}')
else:
    print("\nNo posts to update")
