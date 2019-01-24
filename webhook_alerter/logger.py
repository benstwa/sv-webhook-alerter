import logging

formatter = logging.Formatter(
    '%(asctime)s/+%(relativeCreated)7.0f|'
    '%(levelname)-8s|%(filename)12.12s:%(lineno)-4s |'
    ' %(message)s'
)

logger = logging.getLogger('webhook_alerter')
logger.setLevel(logging.INFO)

# Don't propagate up to the root logger
logger.propagate = False

# Create the console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
