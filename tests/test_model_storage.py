import unittest
from datetime import datetime
from unittest import mock

from freezegun import freeze_time

from dtns import create_app
from dtns import db
from dtns.constants import CommentState
from dtns.constants import PostStatus
from dtns.model_storage import CommentModelStorage
from dtns.model_storage import PostModelStorage
from dtns.model_storage import UserModelStorage
from dtns.models import Comment
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

        user = User(
            email="test_1@test.com", username="test_user_1", password="test_password_1"
        )

        comment = Comment(
            text="A test comment",
            user=user,
            post=self.posts[0],
        )

        db.session.add_all(self.posts + [comment, user])
        db.session.commit()

    def tearDown(self):
        db.session.commit()
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

    def test_get_post_by_slug_returns_none_for_non_exist_post(self):
        post = PostModelStorage.get_post_by_slug("you-wont-findme")

        self.assertIsNone(post)

    def test_get_post_by_slug_include_comments(self):
        post, comments = PostModelStorage.get_post_by_slug(
            "slug-1", include_comments=True
        )

        self.assertIsNotNone(post)
        self.assertIsNotNone(comments)

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

    @freeze_time("2021-12-07")
    def test_publish_post(self):
        post = Post.query.first()

        PostModelStorage.publish_post(post.id)
        published_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(published_post.state, PostStatus.PUBLISHED)
        self.assertIsNotNone(published_post.published_at)
        self.assertNotEqual(published_post.updated_at, post.created_at)

    @freeze_time("2021-12-07")
    def test_archive_post(self):
        post = Post.query.first()

        PostModelStorage.archive_post(post.id)
        archived_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(archived_post.state, PostStatus.ARCHIVED)
        self.assertIsNone(archived_post.published_at)
        self.assertNotEqual(archived_post.updated_at, post.created_at)

    @freeze_time("2021-12-07")
    def test_mark_post_as_draft(self):
        post = Post.query.first()

        PostModelStorage.mark_post_as_draft(post.id)
        draft_post = Post.query.filter_by(id=post.id).first()

        self.assertEqual(draft_post.state, PostStatus.DRAFT)
        self.assertIsNone(draft_post.published_at)
        self.assertNotEqual(draft_post.updated_at, post.created_at)

    def test_search_posts(self):
        post1 = Post(
            title="Fake Title",
            slug="fake-title",
            description="Post description",
            source="Here's a post. Find me later!",
        )
        post2 = Post(
            title="Fake Title 2",
            slug="fake-title-2",
            description="Post description",
            source="Here's a post. Find me later, round two!",
        )
        db.session.add_all([post1, post2])
        db.session.commit()

        # publish one of the new posts
        post = Post.query.filter_by(title="Fake Title").first()

        now = datetime.utcnow()
        post.state = PostStatus.PUBLISHED
        post.updated_at = now
        post.published_at = now

        db.session.add(post)
        db.session.commit()

        found_posts = PostModelStorage.search_posts("find me")

        self.assertIsNotNone(found_posts)
        self.assertEqual(len(found_posts), 1)
        self.assertIn("Find me", found_posts[0].source)

    def test_get_posts_by_month_year(self):
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

        posts = PostModelStorage.get_posts_by_month_year("November 2021")

        self.assertEqual(len(posts), 5)
        for post in posts:
            self.assertEqual(post.published_at.strftime("%B %Y"), "November 2021")


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
        db.session.commit()
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

    def test_get_user_by_email_with_upper_email(self):
        user = UserModelStorage.get_user_by_email("TEST_1@TEST.COM")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test_1@test.com")

    def test_get_user_by_email_returns_none_when_no_email_passed(self):
        user = UserModelStorage.get_user_by_email("")

        self.assertIsNone(user)

    def test_get_user_by_email_returns_none_when_no_user_found_for_email(self):
        user = UserModelStorage.get_user_by_email("wont-find-me@test.com")

        self.assertIsNone(user)

    def test_get_all_for_admin(self):
        users = UserModelStorage.get_all_for_admin()

        self.assertEqual(len(users), NUM_USERS)
        for user in users:
            self.assertIn("id", user)
            self.assertIn("created_at", user)
            self.assertIn("email", user)
            self.assertIn("username", user)
            self.assertIn("is_admin", user)
            self.assertNotIn("password", user)

    def test_get_or_create_comment_user_get_user(self):
        email = "test_1@test.com"
        user = UserModelStorage.get_user_by_email(email)
        self.assertIsNotNone(user)

    def test_get_or_create_comment_user_create_user(self):
        email = "idonotexist@fake.com"
        username = "iamnotreal"
        user = UserModelStorage.get_user_by_email(email)
        self.assertIsNone(user)

        UserModelStorage.get_or_create_comment_user(email, username)

        user = UserModelStorage.get_user_by_email(email)
        self.assertIsNotNone(user)
        self.assertEqual(email, user.email)
        self.assertEqual(username, user.username)
        self.assertEqual("i-only-comment", user.password)
        self.assertFalse(user.is_admin)


class CommentModelStorageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.email = "test_1@test.com"
        self.username = "test_user_1"
        self.user = User(
            email=self.email, username=self.username, password="test_password_1"
        )
        self.user2 = User(
            email="foo@bar.com", username="foobar", password="test_password_2"
        )

        self.post = Post(
            title="Title 1",
            slug="slug-1",
            description="Post description 1",
            source="# Post 1",
        )

        self.comment = Comment(
            text="A test comment",
            user=self.user,
            post=self.post,
        )
        self.comment2 = Comment(
            text="A test comment from a different user",
            user=self.user2,
            post=self.post,
        )

        db.session.add_all([self.user, self.post])
        db.session.commit()

    def tearDown(self):
        db.session.commit()
        db.drop_all()
        self.app_context.pop()

    @mock.patch("dtns.utils.email_utils.send_new_comment_notif")
    def test_create_comment(self, mock_send_new_comment_notif):
        comment_text = "Just leaving a comment!"
        data = {
            "email": self.email,
            "username": self.username,
            "comment": comment_text,
            "post": self.post,
        }

        CommentModelStorage.create_comment(data)
        comment = Comment.query.order_by(-Comment.id).first()

        self.assertIsNotNone(Comment)
        self.assertEqual(comment.text, comment_text)
        self.assertEqual(comment.user_id, self.user.id)
        self.assertEqual(comment.post_id, self.post.id)
        mock_send_new_comment_notif.assert_called_with(comment)

    def test_toggle_visibility_state(self):
        comment = Comment.query.order_by(-Comment.id).first()
        self.assertEqual(comment.state, CommentState.VISIBLE)

        CommentModelStorage.toggle_visibility_state(comment.id)

        comment = Comment.query.order_by(-Comment.id).first()
        self.assertEqual(comment.state, CommentState.HIDDEN)

        CommentModelStorage.toggle_visibility_state(comment.id)

        comment = Comment.query.order_by(-Comment.id).first()
        self.assertEqual(comment.state, CommentState.VISIBLE)

    def test_toggle_visibility_state_no_comment(self):
        comment_id = 100

        result = CommentModelStorage.toggle_visibility_state(comment_id)

        self.assertIsNone(result)

    def test_toggle_visibility_state_raises_exception_bad_state(self):
        self.comment.state = "BREAK"
        db.session.add(self.comment)
        db.session.commit()

        with self.assertRaises(ValueError):
            CommentModelStorage.toggle_visibility_state(self.comment.id)

    def test_get_all_by_user_id(self):
        db.session.add_all([self.comment, self.comment2])
        db.session.commit()
        self.assertEqual(len(CommentModelStorage.get_all()), 2)

        comments = CommentModelStorage.get_all_by_user_id(self.user2.id)

        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].text, self.comment2.text)
