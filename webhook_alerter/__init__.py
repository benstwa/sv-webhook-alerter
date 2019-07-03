import venusian
from pyramid.config import Configurator
from webhook_alerter import views, alerters
from webhook_alerter.alerters.alerters import BaseAlerter


def main(_, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_route('alerter', '/{config}')
    config.scan(views)
    venusian.Scanner().scan(alerters, categories=['alerters'])
    return config.make_wsgi_app()
