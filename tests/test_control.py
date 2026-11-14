import unittest
from unittest.mock import Mock
from cloud_logic import StableWeather,choose_mode
from emotion_control import Device

class TimingTests(unittest.TestCase):
    def test_changes_require_elapsed_time_not_frames(self):
        s=StableWeather()
        for _ in range(1000):self.assertEqual(s.observe('sunny',0),'cloudy')
        self.assertEqual(s.observe('sunny',1.49),'cloudy')
        self.assertEqual(s.observe('sunny',1.5),'sunny')
    def test_flicker_restarts_hold(self):
        s=StableWeather(2.5);s.observe('sunny',0);s.observe('cloudy',2);s.observe('sunny',2.1)
        self.assertEqual(s.observe('sunny',4),'cloudy')
        self.assertEqual(s.observe('sunny',4.7),'sunny')
    def test_absent_face_and_uncertain_predictions_are_neutral(self):
        self.assertEqual(choose_mode(0,'Happiness',1),'cloudy')
        self.assertEqual(choose_mode(1,'Happiness',.2),'cloudy')
        self.assertEqual(choose_mode(1,'Happiness',.9),'sunny')
        self.assertEqual(choose_mode(1,'Sadness',.9),'rainy')
    def test_subtle_expressions_can_trigger_sun_and_rain(self):
        for label, expected in [('Happiness', 'sunny'), ('Surprise', 'sunny'),
                                ('Sadness', 'rainy'), ('Anger', 'rainy'),
                                ('Fear', 'rainy'), ('Disgust', 'rainy')]:
            with self.subTest(label=label):
                self.assertEqual(choose_mode(1, label, .24), 'cloudy')
                self.assertEqual(choose_mode(1, label, .25), expected)
    def test_loss_of_face_can_recover_to_cloudy(self):
        s=StableWeather(2.5);s.observe('sunny',0);s.observe('sunny',3)
        self.assertEqual(s.observe('cloudy',4),'sunny')
        self.assertEqual(s.observe('cloudy',6.5),'cloudy')

class DeviceTests(unittest.TestCase):
    def setUp(self):
        self.session=Mock();self.device=Device('http://device/',self.session)
        self.response=self.session.request.return_value
    def state(self,**kwargs):
        state=dict(version=2,weather='rainy',control='manual');state.update(kwargs)
        self.response.json.return_value=state;return state
    def test_server_manual_choice_is_authoritative(self):
        expected=self.state()
        self.assertEqual(self.device.request('/weather',{'mode':'sunny','source':'auto'}),expected)
        self.assertEqual(self.device.state['weather'],'rainy')
    def test_failed_request_keeps_last_acknowledged_state(self):
        self.state();self.device.request();self.session.request.side_effect=TimeoutError('offline')
        self.assertIsNone(self.device.request('/weather',{'mode':'sunny'}))
        self.assertEqual(self.device.state['weather'],'rainy');self.assertTrue(self.device.error)
    def test_recovers_on_next_success(self):
        self.session.request.side_effect=TimeoutError();self.device.request()
        self.session.request.side_effect=None;self.state(weather='sunny',control='auto')
        self.assertEqual(self.device.request()['weather'],'sunny');self.assertFalse(self.device.error)
    def test_old_firmware_is_explicitly_rejected(self):
        self.response.json.return_value={'weather':'cloudy','camera':True}
        self.assertIsNone(self.device.request());self.assertIn('update required',self.device.error)
    def test_invalid_state_not_accepted(self):
        self.state(weather='nonsense');self.assertIsNone(self.device.request());self.assertIsNone(self.device.state)

if __name__=='__main__':unittest.main()
