import os
from datetime import datetime

import pytest

from lektor._compat import iteritems
from lektor.imagetools import computed_size


def almost_equal(a, b, e=0.00001):
    return abs(a - b) < e


def test_exif(pad):
    image = pad.root.attachments.images.get('test.jpg')
    assert image is not None

    assert image.exif

    assert almost_equal(image.exif.altitude, 779.0293)
    assert almost_equal(image.exif.aperture, 2.275)
    assert image.exif.artist is None
    assert image.exif.camera == 'Apple iPhone 6'
    assert image.exif.camera_make == 'Apple'
    assert image.exif.camera_model == 'iPhone 6'
    assert image.exif.copyright is None
    assert image.exif.created_at == datetime(2015, 12, 6, 11, 37, 38)
    assert image.exif.exposure_time == '1/33'
    assert image.exif.f == u'\u0192/2.2'
    assert almost_equal(image.exif.f_num, 2.2)
    assert image.exif.flash_info == 'Flash did not fire, compulsory flash mode'
    assert image.exif.focal_length == '4.2mm'
    assert image.exif.focal_length_35mm == '29mm'
    assert image.exif.iso == 160
    assert almost_equal(image.exif.latitude, 46.6338333)
    assert image.exif.lens == 'Apple iPhone 6 back camera 4.15mm f/2.2'
    assert image.exif.lens_make == 'Apple'
    assert image.exif.lens_model == 'iPhone 6 back camera 4.15mm f/2.2'
    assert almost_equal(image.exif.longitude, 13.4048333)
    assert image.exif.location == (image.exif.latitude, image.exif.longitude)
    assert image.exif.shutter_speed == '1/33'

    assert image.exif.documentname == 'testName'
    assert image.exif.description == 'testDescription'
    assert image.exif.is_rotated

    assert isinstance(image.exif.to_dict(), dict)

    for key, value in iteritems(image.exif.to_dict()):
        assert getattr(image.exif, key) == value


def test_image_attributes(pad):
    image = pad.root.attachments.images.get('test.jpg')
    assert image is not None

    assert image.width == 512
    assert image.height == 384
    assert image.format == 'jpeg'


@pytest.mark.parametrize(
    [
        'width', 'height', 'source_width', 'source_height',
        'is_rotated', 'expected_width', 'expected_height'
    ],
    [
        # Not rotated.
        # No height specified, calculated proportionally.
        (256, None, 512, 384, False, 256, 192),
        # Height specified but greater than calculated height.
        (256, 256, 512, 384, False, 256, 192),
        # Height specified and less than calculated height with scaled width, so
        # with is scaled down as well.
        (256, 150, 512, 384, False, 200, 150),

        # Rotated image.
        # No height, specified. Image rotated, height used as width and original
        # width scaled proportionally.
        (256, None, 512, 384, True, 256, 341),
        # Height specified.
        (256, 256, 512, 384, True, 192, 256),
        # Height specified and less than rotated width.
        (256, 150, 512, 384, True, 112, 150),
    ]
)
def test_computed_size(
    mocker,
    width,
    height,
    source_width,
    source_height,
    is_rotated,
    expected_width,
    expected_height,
):
    """Test reported width/height are as expected when computing thumb size."""
    with mocker.patch('lektor.imagetools.is_rotated', return_value=is_rotated):
        reported_width, reported_height = computed_size(
            source_image=mocker.MagicMock(),
            width=width,
            height=height,
            actual_width=source_width,
            actual_height=source_height,
            format='jpeg',
        )
    assert (
        (reported_width, reported_height) == (expected_width, expected_height)
    )


def test_thumbnail_height(builder):
    builder.build_all()
    with open(os.path.join(builder.destination_path, 'index.html')) as f:
        html = f.read()

    # Thumbnail is half the original width, so its computed height is half.
    assert '<img src="./test@192.jpg" width="192" height="256">' in html
    # With defined height (tq) matching the computed_height.
    assert '<img src="./test@192x256_q20.jpg" width="192" height="256">' in html
    # With defined height (th) not matching the computed_height, image is scaled
    # proportionally and real thumbnail height is reported.
    assert '<img src="./test@192x192_q30.jpg" width="144" height="192">' in html
    # With cropping enabled the defined with/height will be the exact thumb
    # dimensions.
    assert (
        '<img src="./test@192x192_crop_q40.jpg" width="192" height="192">'
        in html
    )


def test_thumbnail_quality(builder):
    builder.build_all()
    image_file = os.path.join(builder.destination_path, 'test@192x256_q20.jpg')
    image_size = os.path.getsize(image_file)

    # See if the image file with said quality suffix exists
    assert os.path.isfile(image_file)
    # And the filesize is less than 9200 bytes
    assert image_size < 9200
