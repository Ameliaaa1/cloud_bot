"""Run the original enet_b2_8 ONNX graph without importing optional TensorFlow/Torch.
Normalization and class order match installed EmotiEffLib 1.1.1 facial_analysis.py.
The model weights remain in the user's existing EmotiEffLib cache.
"""
from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort

class ExpressionModel:
    labels=['Anger','Contempt','Disgust','Fear','Happiness','Neutral','Sadness','Surprise']
    def __init__(self, model_name='enet_b2_8'):
        if model_name!='enet_b2_8':raise ValueError('This prototype supports enet_b2_8 only')
        path=Path.home()/'.emotiefflib'/f'{model_name}.onnx'
        if not path.is_file():raise FileNotFoundError(f'Model missing: {path}. See EMOTION-CONTROL-README.md')
        opts=ort.SessionOptions();opts.intra_op_num_threads=2
        self.session=ort.InferenceSession(str(path),sess_options=opts,providers=['CPUExecutionProvider'])
        self.input=self.session.get_inputs()[0].name
    def predict_emotions(self,rgb,logits=False):
        x=cv2.resize(rgb,(260,260))/255.
        x=(x-np.array([.485,.456,.406]))/np.array([.229,.224,.225])
        x=x.transpose(2,0,1).astype(np.float32)[None]
        scores=self.session.run(None,{self.input:x})[0]
        if scores.shape!=(1,8) or not np.isfinite(scores).all():raise ValueError('Unexpected model output')
        labels=[self.labels[int(scores[0].argmax())]]
        if not logits:
            scores=np.exp(scores-scores.max(axis=1,keepdims=True));scores/=scores.sum(axis=1,keepdims=True)
        return labels,scores
