import os

from dtns.constants import ALLOWABLE_IMAGE_TYPES


def is_valid_image(filename):
    if filename == "":
        return False

    if not is_valid_image_type(filename):
        return False

    return True


def is_valid_image_type(filename):
    return get_file_ext(filename) in ALLOWABLE_IMAGE_TYPES


def get_file_ext(filename):
    return os.path.splitext(filename)[1].lower()
