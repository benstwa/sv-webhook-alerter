from paste.translogger import TransLogger
from pyramid.config import Configurator
from waitress import serve
from webhook_alerter import views


def main():
    config = Configurator()
    config.include('pyramid_mako')
    config.include('pyramid_debugtoolbar')
    config.add_route('slack_alerter', '/slack_alerter/{config}')
    config.scan(views)
    app = TransLogger(config.make_wsgi_app())
    serve(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
