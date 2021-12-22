import unittest
from datetime import datetime
from unittest import mock

from freezegun import freeze_time

from dtns import create_app
from dtns import db
from dtns.constants import PostStatus
from dtns.model_storage import PostModelStorage
from dtns.models import Post
from dtns.utils import image_utils
from dtns.utils import post_utils

NUM_POSTS = 10


@mock.patch(
    "dtns.utils.image_utils.os.listdir",
    return_value=[
        "test-img-2.jpg",
        "test-img-1.jpg",
        "test-img-3.jpg",
        "test-img-4.tiff",
    ],
)
class ImageManagerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()

    def test_get_all_images(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)

        image_list = image_manager.get_all_images()

        self.assertEqual(
            image_list,
            [
                "test-img-2.jpg",
                "test-img-1.jpg",
                "test-img-3.jpg",
            ],
        )

    def test_get_all_images_sorted_default(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)

        image_list = image_manager.get_all_images_sorted()

        self.assertEqual(
            image_list,
            [
                "test-img-1.jpg",
                "test-img-2.jpg",
                "test-img-3.jpg",
            ],
        )

    def test_get_all_images_sorted_asc_false(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)

        image_list = image_manager.get_all_images_sorted(asc=False)

        self.assertEqual(
            image_list,
            [
                "test-img-3.jpg",
                "test-img-2.jpg",
                "test-img-1.jpg",
            ],
        )

    def test_get_image(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)

        image = image_manager.get_image("test-img-1.jpg")

        self.assertEqual(image, "test-img-1.jpg")

    def test_save_image(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)
        mock_file_upload = mock.MagicMock()
        mock_file_upload.filename = "test-img-5.jpg"
        mock_file_upload.save.return_value = f"/mock_path/{mock_file_upload.filename}"

        image = image_manager.save_image(mock_file_upload)

        self.assertEqual(image, mock_file_upload.filename)

    def test_save_image_invalid_filename_returns_none(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)
        mock_file_upload = mock.MagicMock()
        mock_file_upload.filename = "test-img-5.tiff"
        mock_file_upload.save.return_value = f"/mock_path/{mock_file_upload.filename}"

        image = image_manager.save_image(mock_file_upload)

        self.assertIsNone(image)

    def test_save_image_already_saved_returns_none(self, mock_listdir):
        image_manager = image_utils.ImageManager(self.app)
        mock_file_upload = mock.MagicMock()
        mock_file_upload.filename = "test-img-1.jpg"
        mock_file_upload.save.return_value = f"/mock_path/{mock_file_upload.filename}"

        image = image_manager.save_image(mock_file_upload)

        self.assertIsNone(image)

    @mock.patch("dtns.utils.image_utils.os.remove")
    def test_delete_image(self, mock_remove, mock_listdir):
        mock_remove.return_value = None
        image_manager = image_utils.ImageManager(self.app)

        image = image_manager.delete_image("test-img-2.jpg")

        self.assertEqual(image, "test-img-2.jpg")

    @mock.patch("dtns.utils.image_utils.os.remove")
    def test_delete_image_non_exist_image_returns_none(self, mock_remove, mock_listdir):
        mock_remove.return_value = None
        image_manager = image_utils.ImageManager(self.app)

        image = image_manager.delete_image("wont-find.jpg")

        self.assertIsNone(image)

    def tearDown(self):
        self.app_context.pop()


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
