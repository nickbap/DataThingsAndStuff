import unittest
from datetime import datetime

from freezegun import freeze_time

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.model_storage import PostModelStorage
from dtns.models import Post
from dtns.utils import image_utils
from dtns.utils import post_utils

NUM_POSTS = 10


class ImageUtilsTestCase(unittest.TestCase):
    def test_false_is_returned_for_no_filename(self):
        filename = ""

        result = image_utils.is_valid_image(filename)

        self.assertFalse(result)

    def test_false_is_returned_for_invalid_image_type(self):
        filename = "test-image.tiff"

        result = image_utils.is_valid_image(filename)

        self.assertFalse(result)

    def test_true_is_returned_for_valid_image_type(self):
        filename = "test-image.jpeg"

        result = image_utils.is_valid_image(filename)

        self.assertTrue(result)

    def test_true_is_returned_for_valid_image_type_uppercase(self):
        filename = "test-image.JPG"

        result = image_utils.is_valid_image(filename)

        self.assertTrue(result)


class PostUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create posts
        self.posts = []
        for i in range(NUM_POSTS):
            i += 1
            source = f"# Post {i}"
            post = Post(
                title=f"Title {i}",
                slug=f"slug-{i}",
                description=f"Post description {i}",
                source=source,
            )
            self.posts.append(post)

        db.session.add_all(self.posts)
        db.session.commit()

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    def test_aggregate_and_sort_posts_by_month_year(self):
        # "publish" posts
        for i in range(8):
            post = self.posts[i]
            if i <= 4:
                freezer = freeze_time("2021-11-01 12:00:00")
                freezer.start()

                now = datetime.utcnow()
                post.state = PostStatus.PUBLISHED
                post.updated_at = now
                post.published_at = now

                db.session.add(post)
                db.session.commit()
                freezer.stop()
            else:
                freezer = freeze_time("2021-12-01 12:00:00")
                freezer.start()

                now = datetime.utcnow()
                post.state = PostStatus.PUBLISHED
                post.updated_at = now
                post.published_at = now

                db.session.add(post)
                db.session.commit()
                freezer.stop()

        posts = PostModelStorage.get_all_published_posts()

        post_archive = post_utils.aggregate_and_sort_posts_by_month_year(posts)

        self.assertEqual(post_archive, ["December 2021", "November 2021"])
        self.assertEqual(len(post_archive), 2)
