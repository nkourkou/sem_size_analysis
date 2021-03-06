"""Unit tests for the prediction functions"""

import matplotlib.image as mpimg
from fastai.vision import Learner

from ..src import predict
from ..src.transform_data import fastai_image

from skimage.transform import resize

from pathlib import Path
import numpy as np

import pytest


@pytest.fixture
def learn():
    learn = predict.fetch_learner()
    return learn


def test_fetch_learner(learn):
    """
    Tests fetch_learner in predict by
    asserting the output is of type Learner
    """
    assert isinstance(learn, Learner)


def test_predict_segment(learn):
    """
    Tests predict_segment function in predict
    by asserting the output shape and its unique
    values.
    """
    # load test image
    img_path = (
        Path(__file__).parent
        / 'images'
        / 'train_x'
        / 'L2_0a7efff5757e6b543ee1a0d17328c881.jpg'
    )
    img = mpimg.imread(img_path)

    # transform image to use in model
    img = resize(img, (192, 256), order=1)
    img = fastai_image(img)

    # make prediction and assertions
    pred = predict.predict_segment(learn, img)
    assert pred.shape == (192, 256)
    assert sorted(list(np.unique(pred))) == [0, 1]


def test_get_size_distr():
    """
    Tests get_size_distr function in predict
    by asserting its output shape, number of
    unique values, and mean of the size of the
    connected regions.
    """
    pred = np.array(
        [[0, 0, 0, 0, 0],
         [1, 1, 0, 0, 0],
         [1, 1, 0, 0, 0],
         [0, 0, 1, 1, 1],
         [0, 0, 1, 1, 1]],
        dtype=np.uint8
    )

    labeled, unique, size_distr = predict.get_size_distr(pred)
    assert labeled.shape == (5, 5)
    assert len(unique) == 2
    assert len(size_distr) == 2
    assert np.allclose(size_distr.mean(), 5)
