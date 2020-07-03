import io
import base64
import requests

import torchvision
import torchvision.transforms as transforms
from PIL import Image, ImageDraw
from flask import Flask, render_template, request, redirect

from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)
model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.eval()


def transform_image(image):
    tforms = transforms.Compose([transforms.ToTensor(),
                                 transforms.Normalize(
                                     [0.485, 0.456, 0.406],
                                     [0.229, 0.224, 0.225])])
    return tforms(image).unsqueeze(0) / 255.0


def get_prediction(image):
    tensor = transform_image(image=image)
    outputs = model.forward(tensor)
    return outputs


def plot_preds(source_img, preds):
    boxes = preds['boxes'].detach().numpy()
    draw = ImageDraw.Draw(source_img)
    for box in boxes:
        draw.rectangle(((box[0], box[1]), (box[2], box[3])), outline='red')
    return source_img


@app.route('/', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        url = request.form.get('url')
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            return redirect(request.url)
        image_bytes = r.content
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        preds = get_prediction(image=image)

        CONF_THRESH = 0.5
        boxes = preds[0]['boxes'][preds[0]['scores'] > CONF_THRESH]
        boxes_dict = dict()
        boxes_dict['boxes'] = boxes

        img_with_boxes = plot_preds(image, boxes_dict)
        output = io.BytesIO()
        img_with_boxes.save(output, format='PNG')
        output.seek(0, 0)
        output_s = output.read()
        b64 = base64.b64encode(output_s).decode('ascii')
        return render_template('result.html', img_original=url, img_with_boxes=b64)
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
