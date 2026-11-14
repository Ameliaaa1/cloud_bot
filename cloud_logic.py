"""Pure timing logic, independent of camera/model packages."""
DEFAULT_THRESHOLD = 0.25
DEFAULT_HOLD_SECONDS = 1.5

class StableWeather:
    def __init__(self, hold=DEFAULT_HOLD_SECONDS):
        self.hold=hold
        self.current='cloudy'
        self.candidate=None
        self.since=0.
    def observe(self, mode, now):
        if mode!=self.candidate:
            self.candidate=mode
            self.since=now
        if now-self.since>=self.hold:
            self.current=mode
        return self.current

def choose_mode(face_count, emotion, confidence, threshold=DEFAULT_THRESHOLD, *, smile_threshold=DEFAULT_THRESHOLD):
    required_confidence = smile_threshold if emotion == 'Happiness' else threshold
    if not face_count or confidence < required_confidence:
        return 'cloudy'
    if emotion in {'Happiness','Surprise'}:return 'sunny'
    if emotion in {'Sadness','Anger','Fear','Disgust'}:return 'rainy'
    return 'cloudy'
