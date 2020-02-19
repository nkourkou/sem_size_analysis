from flask import Flask, request
import json
import numpy as np
import gdown

from fastai.vision import load_learner

from . import predict as pred
from . import transform_data as td

# import predict as pred
# import transform_data as td

import base64
import io
from PIL import Image
from pathlib import Path

app = Flask(__name__)
host = 'localhost'
port = '5000'

# load model
try:
    model_path = Path(__file__).parents[1]
    learn = load_learner(model_path, 'stage-2_bs16.pkl')
except IOError:
    url = 'https://drive.google.com/uc?id=1ClEUOwFhIOMNxvedps8WQN8Koy6NT5eI'
    output = 'stage-2_bs16.pkl'
    gdown.download(url, output, quiet=False)

    model_path = Path(__file__).parents[1]
    learn = load_learner(model_path, output)


def b64_2_numpy(string):
    """Converts base64 encoded image to numpy array"""
    decoded = base64.b64decode(string)
    im = Image.open(io.BytesIO(decoded))
    return np.array(im)


def numpy_2_b64(arr, enc_format='png'):
    """Converts numpy array to base64 encoded image"""
    img_pil = Image.fromarray(arr)
    buff = io.BytesIO()
    img_pil.save(buff, format=enc_format)
    return base64.b64encode(buff.getvalue()).decode("utf-8")


@app.route("/")
def hello():
    """Homepage"""
    return "Welcome to the main page!"


@app.route('/api/predict', methods=['POST'])
def predict():
    """Obtains image segmentation prediction on image"""
    # get base64 image from requested json
    content = request.get_json()
    content = content['contents']

    # convert base64 image to numpy array
    content_type, content_string = content.split(',')
    im = b64_2_numpy(content_string)

    # perform data transformations
    if len(im.shape) == 2:
        im = td.make_3channel(im)
    img = td.resize(im, (192, 256))
    img = td.fastai_image(img)

    # make prediction
    prediction = pred.predict_segment(learn, img).numpy()[0]

    # convert prediction array to base64 image and dump relevant data to json
    encoded_pred = content_type + ',' + numpy_2_b64(np.uint8(255*prediction))
    return json.dumps({
            'content_type': content_type,
            'ximage_b64': content,
            'yimage_b64': encoded_pred,
            'yimage_list': prediction.tolist()
    })


@app.route('/api/orig_size_distr', methods=['POST'])
def orig_size_distr():
    """
    Obtains size distribution of image without user input. Also
    returns a version of the labeled image as a 3 channel rgb
    image to be shown on the dashboard.
    """
    # get requested json
    content = request.get_json()
    data_pred = json.loads(content['data_pred'])

    # obtain size distributions on prediction by labeling connected regions
    pred_data = np.asarray(data_pred['yimage_list'], dtype=np.uint8)
    labeled, unique, size_distr = pred.get_size_distr(pred_data)

    # create 1D array mapping unique value to a unique color in decimal
    flattened_color_arr = np.linspace(
        0,
        256 ** 3 - 1,
        num=len(unique) + 1,
        dtype=np.int64
    )

    # represent values in flattened_color_arr as three digit
    # number with base 256 to create a color array with shape
    # (num unique values including background, 3)
    colors = np.zeros((len(unique) + 1, 3), dtype=np.uint8)
    for i in range(len(colors)):
        colors[i] = np.array([
            (flattened_color_arr[i] // (256 ** 2)) % 256,
            (flattened_color_arr[i] // (256)) % 256,
            flattened_color_arr[i] % 256
        ])

    # create a lookup table using colors array and convert 2D labeled array
    # into 3D rgb array
    lookup = np.zeros((len(unique) + 1, 3), dtype=np.uint8)
    lookup[np.unique(labeled - 1)] = colors
    rgb = lookup[labeled - 1]

    # encode rgb array as base64 image as dump relevant data to json
    encoded_rgb = data_pred['content_type'] + ',' + numpy_2_b64(rgb)
    return json.dumps({
            'content_type': data_pred['content_type'],
            'rgb_pred_b64': encoded_rgb,
            'rgb_pred_list': rgb.tolist(),
            'labeled_list': labeled.tolist(),
            'unique_list': unique.tolist(),
            'size_distr_list': size_distr.tolist()
    })


@app.route('/api/clicked_size_distr', methods=['POST'])
def clicked_size_distr():
    """
    Obtains size distribution of image after user has clicked on
    image to indicate which segment they would like to remove.
    """
    # get requested json
    content = request.get_json()
    data_size_distr = json.loads(content['size_distr_json'])
    click = content['click']
    data_pred = json.loads(content['data_pred'])

    # pull previous values from size_distr_json
    rgb = np.asarray(data_size_distr['rgb_pred_list'], dtype=np.uint8)
    labeled = data_size_distr['labeled_list']
    unique = np.asarray(data_size_distr['unique_list'])
    size_distr = np.asarray(data_size_distr['size_distr_list'])

    # remove data based on where the user has clicked
    if click is not None:
        # grab coordinates of where the user clicked
        xclick, yclick = click['points'][0]['x'], click['points'][0]['y']

        # remove all values that match the value located where the user clicked
        remove = np.where(unique == labeled[191 - yclick][xclick])[0]
        unique = np.delete(unique, remove)
        size_distr = np.delete(size_distr, remove)
        click_r, click_g, click_b = rgb[191 - yclick, xclick, :]
        mask = (
            (rgb[:, :, 0] == click_r)
            & (rgb[:, :, 1] == click_g)
            & (rgb[:, :, 2] == click_b)
        )
        rgb[mask] = [0, 0, 0]

    # encode rgb array as base64 image and dump relevant data to json
    encoded_rgb = data_pred['content_type'] + ',' + numpy_2_b64(rgb)
    return json.dumps({
        'content_type': data_pred['content_type'],
        'rgb_pred_b64': encoded_rgb,
        'rgb_pred_list': rgb.tolist(),
        'labeled_list': labeled,
        'unique_list': unique.tolist(),
        'size_distr_list': size_distr.tolist()
    })


if __name__ == '__main__':
    app.run(debug=True, host=host, port=port)