import json
import requests

# Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/
webhook_url = 'https://hooks.slack.com/services/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'

def notify_queueing(match_num):
    send_plain_message("Match number "+str(match_num)+" is ending.")

def team_numbers_on_deck(b1,b2,g1,g2):
    send_plain_message("The following teams are now on deck: \n On the blue side\
, we have team #%i and team #%i \n On the gold side, we\
 have team #%i and team #%i" % (b1,b2,g1,g2))

def team_names_on_deck(b1,b2,g1,g2):
    send_plain_message("The following teams are now on deck: \n On the blue side\
, we have %s and %s \n On the gold side, we\
 have %s and %s" % (b1,b2,g1,g2))

def send_plain_message(message):
    slack_data = {'text': message}
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
        )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
