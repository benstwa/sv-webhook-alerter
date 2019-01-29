import os
import pytz
import hmac
import hashlib
import venusian
import yaml
import pkg_resources
from dateutil.parser import parse

config_path = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse("webhook_alerter"),
    "webhook_alerter/webhook_config/"
)


ALERTERS = {}


class AlertConfig(object):
    def __call__(self, wrapped):
        def callback(_, name, cls):
            ALERTERS[name] = cls
        venusian.attach(wrapped, callback, 'alerters')
        return wrapped


class BaseAlerter(object):
    def __init__(self, secret, timezone, date_format):
        self.secret = secret
        self.timezone = timezone
        self.date_format = date_format

    def check_hash(self, raw_data, hash_):
        if hash_ == hmac.new(self.secret, msg=raw_data, digestmod=hashlib.sha256).hexdigest():
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


def get_alerter(config):
    f_name = config_path + config + '.yaml'
    if os.path.exists(f_name):
        with open(f_name) as f:
            config = yaml.load(f)
            clsname = config['class']
            cls = ALERTERS[clsname]
            return cls(**config)
