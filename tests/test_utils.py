import unittest

from dtns.utils import image_utils


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
