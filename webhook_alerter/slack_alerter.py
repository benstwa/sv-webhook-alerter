import slacker
import time
from webhook_alerter.alerters import BaseAlerter, AlertConfig


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


@AlertConfig()
class SlackAlerter(BaseAlerter):

    # noinspection PyUnusedLocal
    def __init__(self, secret, url, date_format, timezone, slack_params=None, **kwargs):
        BaseAlerter.__init__(self, secret, timezone, date_format)
        self.url = url
        if slack_params:
            self.slack_params = slack_params
        else:
            self.slack_params = {}

    def build_message(self, data):
        state = data['payload']['state']

        alert_dict = super(SlackAlerter, self).build_message(data)

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

        message = {
            'attachments': [
                {
                    'text': TEMPLATES[state] % alert_dict,
                    'color': colour,
                    'ts': int(time.time())
                }
            ]
        }

        message.update(self.slack_params)

        return message

    def send_alert(self, data):
        message = self.build_message(data)

        slacker.IncomingWebhook(self.url).post(message)
