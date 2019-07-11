import logging
from pyramid.view import view_config
from webhook_alerter.alerters.alerters import BaseAlerter

logger = logging.getLogger('webhook_alerter')


@view_config(route_name='alerter', renderer='json')
def api_webhook_alert(request):
    config = request.matchdict['config']
    alerter = BaseAlerter.get_alerter(config)
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
