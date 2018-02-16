import numpy as np
from scipy.signal import fftconvolve
import cv2

_CIRCLE_MASKS = {}


class ImagePrefilter(object):
    def apply(self, frame):
        raise NotImplementedError("`apply` must be implemented in a subclass")


class CLAHEPrefilter(ImagePrefilter):
    DEFAULT_CLIP_LIMIT = 3.0
    DEFAULT_TILE_GRID_SIZE = 8

    def __init__(self, **kwargs):
        self.clip_limit = kwargs.get("clip_limit", self.DEFAULT_CLIP_LIMIT)
        self.tile_grid_size = kwargs.get("tile_grid_size",
                                         self.DEFAULT_TILE_GRID_SIZE)
        self.clahe = cv2.createCLAHE(
            self.clip_limit, (self.tile_grid_size, self.tile_grid_size))
        super(CLAHEPrefilter, self).__init__(**kwargs)

    def apply(self, frame):
        return self.clahe.apply(frame)


_PREFILTERS = {"CLAHE": CLAHEPrefilter}


def get_filter(filter_name, *args, **kwargs):
    try:
        klass = _PREFILTERS[filter_name]
        return klass(*args, **kwargs)
    except KeyError:
        raise ValueError(("{} is an invalid prefilter name. Valid choices are:"
                          " {}").format(filter_name, _PREFILTERS.keys()))


def get_circle_mask(radius):
    """Get circular mask for estimating center point.

    Returns a cached mask if it has already been computed.

    Parameters
    ----------
    radius : int
        Radius in pixels of the circle to draw.

    Returns
    -------
    mask : numpy.ndarray
        Circle mask.
    """
    global _CIRCLE_MASKS
    mask = _CIRCLE_MASKS.get(radius, None)
    if mask is None:
        Y, X = np.meshgrid(np.arange(-radius, radius+1),
                           np.arange(-radius, radius+1))
        mask = np.zeros([2*radius + 1, 2*radius + 1])
        ones = X**2 + Y**2 < radius**2
        mask[ones] = 1
        _CIRCLE_MASKS[radius] = mask
    return mask


def max_image_at_value(image, value):
    """Get an image where pixels closest to `value` are brightest.

    Parameters
    ----------
    image : numpy.ndarray
        Image to transform.
    value : int
        Value to make brightest in the transformed image.

    Returns
    -------
    image : numpy.ndarry
        Transformed image.
    """
    min_at_value = np.abs(image.astype(float) - value)
    return (min_at_value.max() - min_at_value).astype(np.uint8)


def max_convolution_positions(image, kernel, bounding_box=None,
                              mode="same"):
    """Convolve image with kernel and return the max location.

    Convolution is done using fftconvolve with mode set to `mode`. It
    is only performed over the image region within `bounding_box` if it
    is provided. The resulting coordinates are provided in the context
    of the original image.

    Parameters
    ----------
    image : numpy.ndarray
        Image over which to convolve the kernel.
    kernel : numpy.ndarray
        Kernel to convolve with the image.
    bounding_box : numpy.ndarray
        [xmin, xmax, ymin, ymax] bounding box on the image.
    mode : string
        Mode to run fftconvolve with.

    Returns
    -------
    max_position : tuple
        (y, x) mean location maximum of the convolution of the kernel
        with the image.

    Raises
    ------
    ValueError
        If bounding box is provided but incorrectly defined.
    """
    if bounding_box is None:
        cropped_image = image
        xmin = 0
        ymin = 0
    else:
        xmin, xmax, ymin, ymax = bounding_box
        cropped_image = image[ymin:ymax, xmin:xmax]

    conv = fftconvolve(cropped_image, kernel, mode=mode)
    y, x = np.where(conv == np.max(conv))

    return (int(np.mean(y)+ymin), int(np.mean(x)+xmin))
