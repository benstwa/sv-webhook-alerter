from paste.translogger import TransLogger
from pyramid.config import Configurator
from waitress import serve
from webhook_alerter import views
import venusian


def main():
    config = Configurator()
    config.add_route('alerter', '/{config}')
    config.scan(views)
    from webhook_alerter import alerters
    # noinspection PyStatementEffect
    venusian.Scanner().scan(alerters)
    app = TransLogger(config.make_wsgi_app())
    serve(app, host='0.0.0.0', port=8080)
