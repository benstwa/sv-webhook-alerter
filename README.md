# Notice

**Although this has been developed by a SciVisum employee, it should not be considered something developed _by_ SciVisum.**

It is provided purely as a basic example of how to start writing your own web service to interface with SciVisum's web hook alerting feature. It should not be considered complete or production ready. This may change in time if more development is done and more flexibility added.

That said, if anyone finds this useful, and would like to contribute, I am open to pull requests or  feature requests.

***

# Usage

This example has been designed to work with Slack's [incoming webhooks](https://api.slack.com/incoming-webhooks). 

Configuration for endpoints is made in the yml files in the `webhook_config` directory. The Slack URL and the secret key from SciVisum will go in this file. The name of this file becomes part of the URL. For example, with `example.yml`, the URL for that configuration will be `http://yourdomain.com/slack_alerter/example`

# Installation

TODO
