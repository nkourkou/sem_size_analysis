from ..src import config as cf
import numpy as np


def test_path_img():
    assert cf.PATH_IMG.exists()


def test_path_lbl():
    assert cf.PATH_LBL.exists()


def test_codes():
    assert isinstance(cf.CODES, np.ndarray)


def test_input_size():
    assert isinstance(cf.INPUT_SIZE, tuple)


def test_bath_size():
    assert isinstance(cf.BATCH_SIZE, int)


def test_freeze_layer():
    assert isinstance(cf.FREEZE_LAYER, int)


def test_epochs():
    assert isinstance(cf.EPOCHS, int)


def test_learning_rate():
    assert isinstance(cf.LEARNING_RATE, slice)


def test_weight_decay():
    assert isinstance(cf.WEIGHT_DECAY, float)


def test_save_model():
    assert isinstance(cf.SAVE_MODEL, str)


def test_path_to_testing():
    assert cf.PATH_TO_TESTING.exists()
