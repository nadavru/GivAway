try:
    import detectron2
except:
    import os 
    os.system('pip install git+https://github.com/facebookresearch/detectron2.git')

from matplotlib.pyplot import axis
import gradio as gr
import requests
import numpy as np
from torch import nn
import requests

import torch
import detectron2
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
from detectron2.utils.visualizer import ColorMode

from transformers import CLIPProcessor, CLIPModel


def merge_segment(pred_segm):
    merge_dict = {}
    for i in range(len(pred_segm)):
        merge_dict[i] = []
        for j in range(i+1,len(pred_segm)):
            if torch.sum(pred_segm[i]*pred_segm[j])>0:
                merge_dict[i].append(j)
    
    to_delete = []
    for key in merge_dict:
        for element in merge_dict[key]:
            to_delete.append(element)
    
    for element in to_delete:
        merge_dict.pop(element,None)
        
    empty_delete = []
    for key in merge_dict:
        if merge_dict[key] == []:
            empty_delete.append(key)
    
    for element in empty_delete:
        merge_dict.pop(element,None)
        
    for key in merge_dict:
        for element in merge_dict[key]:
            pred_segm[key]+=pred_segm[element]
            
    except_elem = list(set(to_delete))
    
    new_indexes = list(range(len(pred_segm)))
    for elem in except_elem:
        new_indexes.remove(elem)
        
    return pred_segm[new_indexes]

def inference(image, predictor, my_metadata):
    # img = np.array(image.resize((500, height)))
    img = np.array(image)
    outputs = predictor(img)
    out_dict = outputs["instances"].to("cpu").get_fields()
    new_inst = detectron2.structures.Instances((1024,1024))
    new_inst.set('pred_masks',merge_segment(out_dict['pred_masks']))
    v = Visualizer(img[:, :, ::-1],
                   metadata=my_metadata, 
                   scale=0.5, 
                   instance_mode=ColorMode.SEGMENTATION   # remove the colors of unsegmented pixels. This option is only available for segmentation models
    )
    # v = Visualizer(img,scale=1.2)
    #print(outputs["instances"].to('cpu'))
    out = v.draw_instance_predictions(new_inst)
    
    return out.get_image()[:, :, ::-1]
    

def segment_damage(image, predictor, my_metadata):
    return inference(image,predictor, my_metadata)

class Damage_detection:
    def __init__(self, seg_model_path, device):
        model_path = seg_model_path
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.6
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        cfg.MODEL.WEIGHTS = model_path

        cfg.MODEL.DEVICE= str(device)

        self.predictor = DefaultPredictor(cfg)
        self.my_metadata = MetadataCatalog.get("car_dataset_val")
        self.my_metadata.thing_classes = ["damage"]

    def segment_damage(self, image):
        return inference(image,self.predictor, self.my_metadata)

class Clip:
    def __init__(self, device=torch.device("cpu")):
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model = self.clip_model.to(device)
        self.device = device
    
    def get_probabilities_from_image(self, image, labels=['good conditions', 'low damage', 'high damage and wrecked']):
        inputs = self.clip_processor(text=labels, images=image, return_tensors="pt", padding=True).to(self.device)
        outputs = self.clip_model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        probs_dict = {labels[i]: probs[0][i].item() for i in range(len(labels))}
        return probs_dict

if __name__ == '__main__':
    from PIL import Image
    import matplotlib.pyplot as plt

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    print(device)

    seg_model_path = '/Users/gil/HackZurich/Python-Live-Chat-App/models/Car_damage_detection.pth'

    damge = Damage_detection(seg_model_path, device)

    # image_path = '/Users/gil/Downloads/images/images.jpeg'
    image_path = '/Users/gil/Downloads/images/wrecked-honda-car.webp'
    
    image = Image.open(image_path)
    seg_image = damge.segment_damage(image)
    
    fig, (ax1, ax2) = plt.subplots(1, 2)

    ax1.imshow(image)
    ax1.axis('off')  # Turn off axis labels and ticks

    ax2.imshow(seg_image)
    ax2.axis('off')  # Turn off axis labels and ticks

    # Show both images
    plt.show()