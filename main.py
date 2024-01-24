from rich.console import Console

from helper import (add_alts, get_post, get_post_ids, is_post_changed,
                    update_post)

console = Console(tab_size=2)
print = console.print

post_ids = get_post_ids(status="draft")

for post_id in post_ids:
    original_post = get_post(post_id)
    if "Tokenization" in original_post["title"]:  # skip Scott's new post for now
        pass
    else:
        updated_post_data = add_alts(post_id)
        if is_post_changed(original_post, updated_post_data):
            response = update_post(post_id, updated_post_data)
        else:
            print(f"\t- No change needed for [blue]{original_post['title']}[/blue]")
