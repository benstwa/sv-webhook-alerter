from pyramid.view import view_config
from webhook_alerter.logger import logger
from webhook_alerter.slack_alerter import SlackAlerter


@view_config(route_name='slack_alerter', renderer='json')
def api_webhook_alert(request):
    config = request.matchdict['config']
    alerter = SlackAlerter.get_alerter(config)
    if alerter:
        if alerter.check_hash(request.body, request.headers['X-Scivisum-Webhooks-Signature']):
            if request.json['type'] != 'test':
                # noinspection PyBroadException
                try:
                    alerter.send_alert(request.json)
                except Exception:
                    logger.exception("Failed to send Slack alert")
                    logger.error(request.json)
        else:
            logger.error("Hash did not match")
    else:
        logger.error("Could not get alerter")
    return {}
