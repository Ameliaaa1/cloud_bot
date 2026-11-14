"""Local webcam expression cues -> device-owned automatic/manual state.
Images are neither saved nor sent to ESP32. Run start-cloud-bot.cmd on Windows.
"""
from __future__ import annotations
import argparse, logging, time, threading
from pathlib import Path
from cloud_logic import DEFAULT_HOLD_SECONDS, DEFAULT_THRESHOLD, StableWeather, choose_mode

LOG=logging.getLogger('cloud_bot')
WEATHER_NAMES={'sunny':'SUNNY','cloudy':'CLOUDY','rainy':'RAINY'}

class Device:
    def __init__(self,url,session=None):
        import requests
        self.url=url.rstrip('/');self.session=session or requests.Session()
        self.session.trust_env=False
        self.state=None;self.error='not connected'
    def request(self,path='/state',data=None):
        try:
            r=self.session.request('POST' if data is not None else 'GET',self.url+path,data=data,timeout=(.5,1.0))
            r.raise_for_status();state=r.json()
            if state.get('version')!=2:raise ValueError('ESP32 firmware update required (protocol v2)')
            if state.get('weather') not in WEATHER_NAMES or state.get('control') not in {'auto','manual'}:raise ValueError('Invalid device state')
            self.state=state;self.error='';return state
        except Exception as e:
            self.error=str(e);return None
    def close(self):self.session.close()

class Camera:
    """Capture in a daemon so a blocked camera driver cannot freeze the controls."""
    def __init__(self,index,cv):
        self.index=index;self.cv=cv;self.frame=None;self.stamp=0.;self.lock=threading.Lock();self.stop=threading.Event()
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
    def run(self):
        while not self.stop.is_set():
            cam=self.cv.VideoCapture(self.index,self.cv.CAP_DSHOW)
            if not cam.isOpened():cam.release();cam=self.cv.VideoCapture(self.index)
            try:
                while cam.isOpened() and not self.stop.is_set():
                    ok,frame=cam.read()
                    if not ok:break
                    with self.lock:self.frame=frame;self.stamp=time.monotonic()
                    self.stop.wait(.02)
            finally:cam.release()
            self.stop.wait(2.)
    def latest(self):
        with self.lock:return (None if self.frame is None else self.frame.copy()),self.stamp
    def close(self):self.stop.set();self.thread.join(timeout=.5)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--url',default='http://192.168.4.1');p.add_argument('--camera',type=int,default=0)
    p.add_argument('--model',default='enet_b2_8');p.add_argument('--threshold',type=float,default=DEFAULT_THRESHOLD)
    p.add_argument('--smile-threshold', type=float, default=DEFAULT_THRESHOLD, help='Confidence required to treat a smile as sunny')
    p.add_argument('--hold',type=float,default=DEFAULT_HOLD_SECONDS);p.add_argument('--interval',type=float,default=1.0)
    p.add_argument('--window',default='cloud_bot');p.add_argument('--engine',choices=['emotieff','haar'],default='emotieff')
    p.add_argument('--check',action='store_true',help='Check device protocol without opening a camera')
    a=p.parse_args(argv)
    if not 0<=a.threshold<=1 or not 0<=a.smile_threshold<=1 or a.hold<0 or a.interval<.2:p.error('invalid threshold, hold or interval')
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    device=Device(a.url)
    if a.check:
        try:
            state=device.request();print(state if state else device.error);return 0 if state else 1
        finally:device.close()
    import cv2 as cv
    import numpy as np
    recognizer=None
    if a.engine=='emotieff':
        try:
            from expression_model import ExpressionModel
            recognizer = ExpressionModel(a.model)
        except Exception as e:
            LOG.error('Cannot load expression model: %s. First use needs Internet and a cached model.',e);device.close();return 1
    cascade=Path(cv.data.haarcascades)
    faces_model=cv.CascadeClassifier(str(cascade/'haarcascade_frontalface_default.xml'))
    smiles_model=cv.CascadeClassifier(str(cascade/'haarcascade_smile.xml')) if a.engine=='haar' else None
    stable=StableWeather(a.hold);cam=Camera(a.camera,cv)
    last_analysis=last_frame_stamp=last_network=-1e9;faces=0;emotion=None;confidence=0.;desired='cloudy';last_message=None
    LOG.info('Started %s. a=auto s/c/r=manual q=quit. Device owns control mode.',a.engine)
    try:
        while True:
            now=time.monotonic();frame,stamp=cam.latest();fresh=frame is not None and now-stamp<2
            if fresh and stamp!=last_frame_stamp and now-last_analysis>=.7:
                gray=cv.cvtColor(frame,cv.COLOR_BGR2GRAY);boxes=faces_model.detectMultiScale(gray,1.1,5,minSize=(80,80));faces=len(boxes);emotion=None;confidence=0.
                if faces:
                    x,y,w,h=max(boxes,key=lambda b:b[2]*b[3]);pad=int(.15*max(w,h));crop=frame[max(0,y-pad):min(frame.shape[0],y+h+pad),max(0,x-pad):min(frame.shape[1],x+w+pad)]
                    try:
                        if recognizer:
                            labels,scores=recognizer.predict_emotions(cv.cvtColor(crop,cv.COLOR_BGR2RGB),logits=False)
                            emotion=str(labels[0]);confidence=float(max(scores[0]))
                        else:
                            found=smiles_model.detectMultiScale(gray[y:y+h,x:x+w],1.7,22,minSize=(35,20));emotion='Happiness' if len(found) else 'Neutral';confidence=1. if len(found) else 0.
                    except Exception as e:LOG.warning('Inference failed: %s',e)
                desired=stable.observe(choose_mode(faces,emotion,confidence,a.threshold,smile_threshold=a.smile_threshold),now)
                last_analysis=now;last_frame_stamp=stamp
            if not fresh:
                faces=0;emotion=None;confidence=0.;desired=stable.observe('cloudy',now)
                frame=np.full((480,800,3),235,dtype=np.uint8)
            if now-last_network>=a.interval:
                state=device.request('/weather',{'mode':desired,'source':'auto'})
                last_network=now
                message=(state['control'],state['weather']) if state else ('offline',device.error)
                if message!=last_message:LOG.info('%s',message);last_message=message
            state=device.state or {};active=state.get('weather','unknown');control=state.get('control','unknown')
            # Opaque light panel keeps the requested black type readable on every background.
            cv.rectangle(frame,(0,0),(frame.shape[1],100),(245,245,245),-1)
            lines=[f'Device: {control.upper()} / {active.upper()} | '+('ONLINE' if not device.error else 'OFFLINE (last known)'),f'faces: {faces} | cue: {emotion or "none"} {confidence:.0%} | proposal: {desired}', 'a=auto  s=sunny  c=cloudy  r=rainy  q=quit'+(' | camera reconnecting' if not fresh else '')]
            for i,line in enumerate(lines):cv.putText(frame,line,(10,24+28*i),cv.FONT_HERSHEY_SIMPLEX,.5,(0,0,0),1,cv.LINE_AA)
            cv.imshow(a.window,frame);key=cv.waitKey(20)&255
            if key in (ord('q'),27):break
            if cv.getWindowProperty(a.window,cv.WND_PROP_VISIBLE)<1:break
            if key==ord('a'):device.request('/control',{'mode':'auto'})
            elif key in (ord('s'),ord('c'),ord('r')):device.request('/weather',{'mode':{ord('s'):'sunny',ord('c'):'cloudy',ord('r'):'rainy'}[key],'source':'manual'})
    except KeyboardInterrupt:pass
    finally:cam.close();device.close();cv.destroyAllWindows()
    return 0
if __name__=='__main__':raise SystemExit(main())
