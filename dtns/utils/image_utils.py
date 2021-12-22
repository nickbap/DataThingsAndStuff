import os

from werkzeug.utils import secure_filename

from dtns.constants import ALLOWABLE_IMAGE_TYPES

image_list_template = """
    <div id="images" class="container d-flex flex-wrap">
        {% for image in image_list %}
        <div class="p-2">
            <div class="d-flex justify-content-center">
                <figure class="figure">
                    <img class="img-thumbnail" style="max-width: 300px; height:auto"
                        src="static/uploads/{{ image }}">
                    <figcaption class="figure-caption">
                        {{ url_for('main.download_file', name=image, _external=True) }}</figcaption>
                </figure>
            </div>
        </div>
        {% endfor %}
    </div>
    """


class ImageManager:
    def __init__(self, app):
        self.app = app

    @property
    def upload_path(self):
        return os.path.join(self.app.static_folder, self.app.config["UPLOAD_FOLDER"])

    def get_all_images(self):
        return [
            image
            for image in os.listdir(self.upload_path)
            if is_valid_image_type(image)
        ]

    def get_all_images_sorted(self, asc=True):
        if not asc:
            return sorted(self.get_all_images(), reverse=True)

        return sorted(self.get_all_images())

    def get_image(self, image_name):
        image = [image for image in self.get_all_images() if image == image_name]
        if image:
            return image[0]
        return

    def save_image(self, file_upload):
        if (
            is_valid_image(file_upload.filename)
            and file_upload.filename not in self.get_all_images()
        ):
            filename = secure_filename(file_upload.filename)
            file_upload.save(os.path.join(self.upload_path, filename))
            return filename
        return

    def delete_image(self, image_name):
        image = self.get_image(image_name)
        if image:
            os.remove(os.path.join(self.upload_path, image_name))
            return image_name
        return


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
