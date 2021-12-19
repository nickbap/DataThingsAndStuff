from datetime import datetime

post_list_template = """
    <div class="text-center pb-1">
        <span>Results for: "{{ criteria }}" <a class="text-reset" href="{{ url_for('main.index') }}"><i
                    class="bi bi-x"></i></a></span>
    </div>
    {% for post in posts %}
        <div class="border p-4 mb-2 shadow-sm">
            <h3 class="mb-0">{{ post.title }}</h3>
            <p class="mb-1 text-muted">{{ post.published_at.strftime('%B %-d, %Y') }}</p>
            <p class="card-text mb-auto">{{ post.description }}</p>
            <a href="{{ url_for('main.post', slug=post.slug) }}">Continue reading</a>
        </div>
    {% endfor %}
    """


def aggregate_and_sort_posts_by_month_year(posts):
    archive_posts = list({post.published_at.strftime("%B %Y") for post in posts})
    return sorted(
        archive_posts,
        key=lambda post: datetime.strptime(post, "%B %Y"),
        reverse=True,
    )
