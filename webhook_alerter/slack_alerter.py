import os
import hmac
import hashlib
import json
import warnings
import yaml
import pkg_resources
import requests
import time
from dateutil.parser import parse

from webhook_alerter.date_utils import datetime_to_local

config_path = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse("webhook_alerter"),
    "webhook_alerter/webhook_config/"
)


DOWN_MESSAGE = """
User Journey "%(name)s" (%(uj_id)s) failed on %(sample_time)s.

Cause(s):
%(causes)s

Sample link: %(sample_link)s
"""

STILL_DOWN_MESSAGE = """
User Journey "%(name)s" (%(uj_id)s) is still down on %(sample_time)s.

Cause(s):
%(causes)s

Sample link: %(sample_link)s
"""

ESCALATED_MESSAGE = """
This is an escalated alert that User Journey "%(name)s" (%(uj_id)s) has not yet recovered on %(sample_time)s.

Cause(s):
%(causes)s

Sample link: %(sample_link)s
"""

RECOVERY = """
User Journey "%(name)s" (%(uj_id)s) has now RECOVERED on %(sample_time)s.

Sample link: %(sample_link)s
"""

TEMPLATES = {
    'DOWN': DOWN_MESSAGE,
    'STILL DOWN': STILL_DOWN_MESSAGE,
    'DOWN (ESCALATION LEVEL 1)': STILL_DOWN_MESSAGE,
    'DOWN (ESCALATION LEVEL 2)': STILL_DOWN_MESSAGE,
    'RECOVERED': RECOVERY
}


class SlackAlerter(object):

    # noinspection PyUnusedLocal
    def __init__(self, secret, url, date_format, timezone, slack_params=None, **kwargs):
        self.secret = secret
        self.url = url
        self.date_format = date_format
        self.timezone = timezone
        if slack_params:
            self.slack_params = slack_params
        else:
            self.slack_params = {}

    @classmethod
    def get_alerter(cls, config):
        f_name = config_path + config + '.yml'
        print f_name
        if os.path.exists(f_name):
            with open(f_name) as f:
                config = yaml.load(f)
                return cls(**config)

    def check_hash(self, raw_data, hash_):
        if hash_ == hmac.new(self.secret, msg=raw_data, digestmod=hashlib.sha256).hexdigest():
            return True

    def _format_time(self, sample_time):
        return sample_time.strftime(self.date_format)

    def send_alert(self, data):
        state = data['payload']['state']

        time_str = data['payload']['time']
        sample_time = parse(time_str)

        sample_time = datetime_to_local(sample_time, timezone=self.timezone)
        sample_time = self._format_time(sample_time)

        alert_dict = {
            'sample_time': sample_time,
            'sample_link': data['payload']['sample']['url'],
            'name': data['payload']['uj']['name'],
            'uj_id': data['payload']['uj']['id']
        }

        if state != 'RECOVERED':
            cause_string = ""

            def step_string(step):
                return " - %s in step %s: %s" % (step['message'], step['step']['number'], step['step']['name'])

            causes = data['payload']['sample']['causes']
            if 'slows' in causes:
                slows = causes['slows']
                if 'fullSample' in slows:
                    cause_string += slows['fullSample']['message']
                    cause_string += "\n\n"
                if 'byStep' in slows:
                    for step in slows['byStep']:
                        cause_string += step_string(step)
                        cause_string += "\n\n"
            if 'errors' in causes:
                errors = causes['errors']
                for step in errors['byStep']:
                    cause_string += step_string(step)
                    cause_string += "\n"
            alert_dict['causes'] = cause_string[:-2]

        if 'causedBy' in data['payload']:
            if data['payload']['causedBy'] in ('ERRORS', 'ERRORS AND SLOWS'):
                colour = '#ff0000'
            elif data['payload']['causedBy'] == 'SLOWS':
                colour = '#800080'
            else:
                raise Exception("causedBy was not SLOWS or ERRORS")
        else:
            colour = '#008000'

        data = {
            'attachments': [
                {
                    'text': TEMPLATES[state] % alert_dict,
                    'color': colour,
                    'ts': int(time.time())
                }
            ]
        }

        data.update(self.slack_params)

        # requests complains about the SSL cert slack use
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", ".*Certificate has no `subjectAltName`.*")
            requests.post(
                self.url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )
