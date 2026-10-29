"""cloud_bot phase 2: local webcam -> EmotiEffLib expression cue -> ESP32 weather."""
from __future__ import annotations
import argparse, time
from collections import deque
from pathlib import Path
import cv2, requests
WEATHER_NAMES={"sunny":"晴天","cloudy":"阴天","rainy":"雨天"}
def choose_mode(face_count, emotion, confidence):
    if face_count==0:return "cloudy"
    if emotion in {"Happiness","Surprise"} and confidence>=0.45:return "sunny"
    if emotion in {"Sadness","Anger","Fear","Disgust"} and confidence>=0.45:return "rainy"
    return "cloudy"
def send_weather(base_url,mode,timeout=1.5):
    try:
        r=requests.post(f"{base_url.rstrip('/')}/weather",data={"mode":mode},timeout=timeout); r.raise_for_status(); return True
    except requests.RequestException:return False
def main():
    p=argparse.ArgumentParser(); p.add_argument("--url",default="http://192.168.4.1"); p.add_argument("--camera",type=int,default=0); p.add_argument("--interval",type=float,default=1.0); p.add_argument("--window",default="cloud_bot emotion prototype"); p.add_argument("--model",default="enet_b2_8"); p.add_argument("--engine",choices=("emotieff","deepface","haar"),default="emotieff"); a=p.parse_args()
    casc=Path(cv2.data.haarcascades); face_cascade=cv2.CascadeClassifier(str(casc/"haarcascade_frontalface_default.xml")); smile_cascade=cv2.CascadeClassifier(str(casc/"haarcascade_smile.xml"))
    recognizer=None; deepface=None
    if a.engine=="emotieff":
        from emotiefflib.facial_analysis import EmotiEffLibRecognizer
        recognizer=EmotiEffLibRecognizer(engine="onnx",model_name=a.model)
    elif a.engine=="deepface":
        from deepface import DeepFace
        deepface=DeepFace
    cam=cv2.VideoCapture(a.camera,cv2.CAP_DSHOW)
    if not cam.isOpened():cam=cv2.VideoCapture(a.camera)
    if not cam.isOpened():raise RuntimeError(f"Cannot open webcam index {a.camera}")
    history=deque(maxlen=5); current=""; forced=None; last_sent=0.; last_ok=False; last_analysis=0.; emotion=None; confidence=0.; faces=0; smiles=0
    print(f"cloud_bot emotion control started ({a.engine})")
    try:
        while True:
            ok,frame=cam.read()
            if not ok:break
            now=time.monotonic()
            if now-last_analysis>=0.7:
                gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); detected=face_cascade.detectMultiScale(gray,1.1,5,minSize=(80,80)); faces=len(detected); smiles=0
                if faces:
                    x,y,w,h=max(detected,key=lambda b:b[2]*b[3]); pad=int(0.15*max(w,h)); x0=max(0,x-pad); y0=max(0,y-pad); x1=min(frame.shape[1],x+w+pad); y1=min(frame.shape[0],y+h+pad); crop=cv2.cvtColor(frame[y0:y1,x0:x1],cv2.COLOR_BGR2RGB); cv2.rectangle(frame,(x,y),(x+w,y+h),(160,190,255),2)
                    try:
                        if a.engine=="emotieff":
                            labels, scores=recognizer.predict_emotions(crop,logits=False); emotion=labels[0]; confidence=float(max(scores[0]))
                        elif a.engine=="deepface":
                            result=deepface.analyze(frame,actions=["emotion"],detector_backend="opencv",enforce_detection=False,silent=True); result=result[0] if isinstance(result,list) else result; emotion=str(result.get("dominant_emotion","")).title() or None; probs=result.get("emotion",{}); confidence=float(probs.get(emotion.lower(),0.))/100. if emotion else 0.
                        else:
                            found=smile_cascade.detectMultiScale(gray[y:y+h,x:x+w],1.7,22,minSize=(35,20)); smiles=len(found); emotion="Happiness" if smiles else "Neutral"; confidence=1. if smiles else 0.
                    except Exception: emotion,confidence=None,0.
                else: emotion,confidence=None,0.
                last_analysis=now
            automatic=choose_mode(faces,emotion,confidence); history.append(automatic); target=forced or max(set(history),key=history.count); retry=(not last_ok and now-last_sent>=3.)
            if (target!=current or retry) and now-last_sent>=a.interval: last_ok=send_weather(a.url,target); current,last_sent=target,now; print(f"{WEATHER_NAMES[target]} ({'sent' if last_ok else 'offline'})")
            shown=current or target; cue=f"{emotion or 'none'} {confidence:.0%}"; status=f"mode: {WEATHER_NAMES[shown]} | faces: {faces} | emotion: {cue}"+(" | manual" if forced else "")
            if not last_ok and now-last_sent<3:status+=" | ESP32 offline?"
            cv2.putText(frame,status,(12,28),cv2.FONT_HERSHEY_SIMPLEX,.58,(0,0,0),2); cv2.putText(frame,"a=auto  s=sunny  c=cloudy  r=rainy  q=quit",(12,55),cv2.FONT_HERSHEY_SIMPLEX,.52,(0,0,0),1); cv2.imshow(a.window,frame)
            key=cv2.waitKey(1)&0xFF
            if key in (ord("q"),27):break
            if key==ord("a"):forced=None
            elif key in (ord("s"),ord("c"),ord("r")):forced={ord("s"):"sunny",ord("c"):"cloudy",ord("r"):"rainy"}[key]
    finally:cam.release(); cv2.destroyAllWindows()
    return 0
if __name__=="__main__":raise SystemExit(main())

