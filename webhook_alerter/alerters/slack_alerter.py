import time
import slacker
import logging
from webhook_alerter.alerters.alerters import BaseAlerter, alerter_config


logger = logging.getLogger('webhook_alerter')


@alerter_config
class SlackWebhookAlerter(BaseAlerter):

    # noinspection PyUnusedLocal
    def __init__(self, secret, url, date_format, timezone, templates, slack_params=None, **kwargs):
        BaseAlerter.__init__(self, secret, timezone, date_format, templates)
        self.url = url
        if slack_params:
            self.slack_params = slack_params
        else:
            self.slack_params = {}
        self.slack = slacker.IncomingWebhook(self.url)

    def build_message(self, data: dict) -> dict:
        state = data['payload']['state']

        alert_dict = super(SlackWebhookAlerter, self).build_message(data)

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
                    cause_string += "\n\n"
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

        template = self.get_template(state)

        message = {
            'attachments': [
                {
                    'text': template % alert_dict,
                    'color': colour,
                    'ts': int(time.time())
                }
            ]
        }

        message.update(self.slack_params)

        return message

    def callback(self, event):
        try:
            response = event.result()
            response.raise_for_status()
        except Exception as e:
            logger.exception(
                "Error from webhook %s: %s" % (self.url, e),
            )
        else:
            logger.info(
                "Webhook %s responded with status %s" % (self.url, response.status_code)
            )

    def send_alert(self, data):
        message = self.build_message(data)
        self.send(lambda: self.slack.post(message), self.callback)
