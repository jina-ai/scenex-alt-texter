from rich.console import Console

from helper import (add_alts, create_alt_text, get_ghost_token, get_post,
                    get_post_ids, is_post_changed, update_post)

console = Console(tab_size=2)
print = console.print


def run_test():
    # get dummy post
    post_id = "65ae57f88da8040001e16ec5"

    original_post = get_post(post_id)
    updated_post_data = add_alts(post_id)

    if is_post_changed(original_post, updated_post_data):
        response = update_post(post_id, updated_post_data)

        print(response)
    else:
        print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")


run_test()

post_ids = get_post_ids(status="draft")
for post_id in post_ids:
    original_post = get_post(post_id)
    print(original_post["title"])

# for post_id in post_ids:
# updated_post_data = add_alts(post_id)

# if is_post_changed(original_post, updated_post_data):
# response = update_post(post_id, updated_post_data)

# print(response)
# else:
# print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")
