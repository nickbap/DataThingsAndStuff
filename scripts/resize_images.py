import glob
import os

import click
from PIL import Image


def _get_file_list(image_dir):
    """
    Get a list of .JPGs for given directory
    """
    file_list = sorted(
        [
            file
            for file in glob.glob(os.path.join(image_dir, "*.JPG"))
            if "_resize" not in file
        ]
    )
    return file_list


def _get_image_rename_lookup(file_list, resize_name):
    """
    Create a lookup for renaming the images
    """
    lookup = {}
    for index, element in enumerate(sorted(file_list), start=1):
        old_filename = element.split("/")[-1]
        new_filename = f"{resize_name}_{str(index).rjust(2, '0')}.JPG"

        lookup[element] = element.replace(old_filename, new_filename)
    return lookup


def _resize_rename_images(lookup, dry_run):
    """
    Resize image and save with new name
    """
    count = 0
    for old_name, new_name in lookup.items():
        if dry_run:
            old_image_name = old_name.split("/")[-1]
            new_image_name = new_name.split("/")[-1]

            rename_output = f"'{old_image_name}' will become: '{new_image_name}'\n"

            click.echo(rename_output)
            count += 1
            continue

        old_img = Image.open(old_name)

        new_img = old_img.resize((1000, 666), Image.LANCZOS)
        old_img.close()

        new_img.save(new_name, optimize=True, quality="web_maximum")
        new_img.close()
        count += 1
    return count


@click.command()
@click.option(
    "--image-dir",
    prompt="Where are the images located?",
    help="The path where the images are located.",
)
@click.option(
    "--resize-name",
    prompt="What should the images be renamed to?",
    help="The new name of the images.",
)
@click.option(
    "--dry-run",
    prompt="Do you want to do a test first?",
    is_flag=True,
    help="See the changes before actually making them.",
)
def resize_images(image_dir, resize_name, dry_run):
    """
    A simple script for resizing and compressing images (.JPG)
    """
    click.echo(f"Looking for images to resize in: {image_dir}")
    click.echo(f"Images will be renamed with: {resize_name}")

    file_list = _get_file_list(image_dir)

    click.echo(f"{len(file_list)} images found in: {image_dir}")

    lookup = _get_image_rename_lookup(file_list, resize_name)

    resize_count = _resize_rename_images(lookup, dry_run)

    click.echo(
        f"{resize_count} images{' would be ' if dry_run else ' '}resized and renamed!"
    )


if __name__ == "__main__":
    resize_images()
