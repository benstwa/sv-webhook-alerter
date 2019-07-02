import os
import pytz
import hmac
import hashlib
import venusian
import yaml
import pkg_resources
from concurrent import futures
from dateutil.parser import parse

config_path = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse("webhook_alerter"),
    "webhook_alerter/webhook_config/"
)


TEMPLATES = {
    'DOWN': 'down',
    'STILL DOWN': 'still_down',
    'DOWN (ESCALATION LEVEL 1)': 'escalated',
    'DOWN (ESCALATION LEVEL 2)': 'escalated',
    'RECOVERED': 'recovery'
}


def alerter_config(func):
    def callback(_, name, cls):
        BaseAlerter.alerters[name] = cls
    venusian.attach(func, callback, 'alerters')
    return func


class BaseAlerter(object):

    _executor = futures.ThreadPoolExecutor(max_workers=5)
    alerters = {}

    def __init__(self, secret, timezone, date_format, templates):
        self.secret = secret
        self.timezone = timezone
        self.date_format = date_format
        self.templates = templates

    def check_hash(self, raw_data, hash_):
        if hash_ == hmac.new(self.secret.encode('utf-8'), msg=raw_data, digestmod=hashlib.sha256).hexdigest():
            return True

    def _localize_time(self, sample_time):
        local_tz = pytz.timezone(self.timezone)
        sample_time = sample_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(sample_time)

    def _format_time(self, sample_time):
        return sample_time.strftime(self.date_format)

    def build_message(self, data):
        time_str = data['payload']['time']
        sample_time = parse(time_str)

        sample_time = self._localize_time(sample_time)
        sample_time = self._format_time(sample_time)

        alert_dict = {
            'sample_time': sample_time,
            'sample_link': data['payload']['sample']['url'],
            'name': data['payload']['uj']['name'],
            'uj_id': data['payload']['uj']['id']
        }

        return alert_dict

    def get_template(self, type_):
        return self.templates[TEMPLATES[type_]]

    def send(self, f, callback):
        future = self._executor.submit(f)
        future.add_done_callback(callback)

    @classmethod
    def get_alerter(cls, config):
        f_name = config_path + config + '.yml'
        if os.path.exists(f_name):
            with open(f_name) as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
                klsname = config['class']
                kls = cls.alerters[klsname]
                return kls(**config)
