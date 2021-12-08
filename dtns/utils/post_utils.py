from datetime import datetime


def aggregate_and_sort_posts_by_month_year(posts):
    archive_posts = list({post.published_at.strftime("%B %Y") for post in posts})
    return sorted(
        archive_posts,
        key=lambda post: datetime.strptime(post, "%B %Y"),
        reverse=True,
    )
