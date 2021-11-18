import unittest
from datetime import datetime

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.model_storage import PostModelStorage
from dtns.model_storage import UserModelStorage
from dtns.models import Post
from dtns.models import User

NUM_POSTS = 10
NUM_USERS = 3


class PostModelStorageTestCase(unittest.TestCase):
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
        db.drop_all()
        self.app_context.pop()

    def test_get(self):
        post = PostModelStorage.get(3)

        self.assertIsNotNone(post)
        self.assertEqual(post.id, 3)

    def test_get_first(self):
        post = PostModelStorage.get_first()

        self.assertIsNotNone(post)
        self.assertEqual(post.id, 1)

    def test_get_all(self):
        posts = PostModelStorage.get_all()

        self.assertEqual(len(posts), NUM_POSTS)

    def test_filter_(self):
        posts = PostModelStorage.filter_(title="Title 1")

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, "Title 1")

        posts = PostModelStorage.filter_(description="Post description 2")

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].description, "Post description 2")

    def test_get_all_published_posts(self):
        # "publish" posts
        for i in range(8):
            post = self.posts[i]

            now = datetime.utcnow()
            post.state = PostStatus.PUBLISHED
            post.updated_at = now
            post.published_at = now

            db.session.add(post)
            db.session.commit()

        posts = PostModelStorage.get_all_published_posts()

        self.assertEqual(len(posts), 8)
        self.assertTrue(
            posts,
            sorted(self.posts[:8], key=lambda post: post.published_at, reverse=True),
        )
        self.assertTrue(all([post.state == PostStatus.PUBLISHED for post in posts]))

    def test_get_recent_posts(self):
        # "publish" posts
        for i in range(6):
            post = self.posts[i]

            now = datetime.utcnow()
            post.state = PostStatus.PUBLISHED
            post.updated_at = now
            post.published_at = now

            db.session.add(post)
            db.session.commit()

        posts = PostModelStorage.get_recent_posts()

        self.assertEqual(len(posts), 5)
        self.assertTrue(
            posts,
            sorted(self.posts[:5], key=lambda post: post.published_at, reverse=True),
        )
        self.assertTrue(all([post.state == PostStatus.PUBLISHED for post in posts]))

    def test_get_all_posts_ordered_by_updated_at(self):
        posts = PostModelStorage.get_all_posts_ordered_by_updated_at()

        self.assertEqual(len(posts), 10)
        self.assertEqual(
            posts, sorted(self.posts, key=lambda post: post.updated_at, reverse=True)
        )

    def test_get_post_by_slug(self):
        post = PostModelStorage.get_post_by_slug("slug-5")

        self.assertIsNotNone(post)
        self.assertTrue(post.slug, "slug-5")

    def test_create_post(self):
        data = {
            "title": "A Fake Post for Testing",
            "slug": "a-fake-post-for-testing",
            "description": "Nothing to see here, this is fake.",
            "source": "#Fake Post Body",
        }

        PostModelStorage.create_post(data)
        post = Post.query.order_by(-Post.id).first()

        self.assertIsNotNone(post)
        self.assertEqual(post.title, data["title"])
        self.assertEqual(post.slug, data["slug"])
        self.assertEqual(post.description, data["description"])
        self.assertEqual(post.source, data["source"])

    def test_edit_post(self):
        post = Post.query.first()
        updated_source = "This a Brand New Shiny update!"
        data = {
            "title": post.title,
            "slug": post.slug,
            "description": post.description,
            "source": updated_source,
        }

        PostModelStorage.edit_post(post.id, data)
        updated_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(updated_post.title, post.title)
        self.assertEqual(updated_post.slug, post.slug)
        self.assertEqual(updated_post.description, post.description)
        self.assertEqual(updated_post.source, updated_source)
        self.assertFalse(updated_post.updated_at < post.updated_at)

    def test_publish_post(self):
        post = Post.query.first()

        PostModelStorage.publish_post(post.id)
        published_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(published_post.state, PostStatus.PUBLISHED)
        self.assertIsNotNone(published_post.published_at)
        self.assertNotEqual(published_post.updated_at, post.created_at)

    def test_archive_post(self):
        post = Post.query.first()

        PostModelStorage.archive_post(post.id)
        archived_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(archived_post.state, PostStatus.ARCHIVED)
        self.assertIsNone(archived_post.published_at)
        self.assertNotEqual(archived_post.updated_at, post.created_at)

    def test_mark_post_as_draft(self):
        post = Post.query.first()

        PostModelStorage.mark_post_as_draft(post.id)
        draft_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(draft_post.state, PostStatus.DRAFT)
        self.assertIsNone(draft_post.published_at)
        self.assertNotEqual(draft_post.updated_at, post.created_at)


class UserModelStorageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        for i in range(NUM_USERS):
            i += 1
            self.email = f"test_{i}@test.com"
            self.username = f"test_user_{i}"
            self.password = f"test_password_{i}"

            user = User(
                email=self.email, username=self.username, password=self.password
            )

            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        db.drop_all()
        self.app_context.pop()

    def test_get(self):
        user = UserModelStorage.get(2)

        self.assertIsNotNone(user)
        self.assertEqual(user.id, 2)

    def test_get_first(self):
        user = UserModelStorage.get_first()

        self.assertIsNotNone(user)
        self.assertEqual(user.id, 1)

    def test_get_all(self):
        users = UserModelStorage.get_all()

        self.assertEqual(len(users), NUM_USERS)

    def test_filter_(self):
        user = UserModelStorage.filter_(username="test_user_3")

        self.assertEqual(len(user), 1)
        self.assertEqual(user[0].username, "test_user_3")

    def test_get_user_by_email(self):
        user = UserModelStorage.get_user_by_email("test_1@test.com")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test_1@test.com")