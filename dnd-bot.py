import argparse
import html
import json
import os
import requests
import shlex
import urllib.parse

from d20 import roll
from flask import abort, Flask, request


app = Flask(__name__)

# Set response type
response_type = "in_channel"  # ephemeral

# Character lookup for anyone with a real name and image.
# Each key/value pair should be in the form of:
# 'command_name': {'name': 'Display Name', 'image': 'url to image to display'}
c_map = {
    'drizzt': {
        'name': "Drizzt Do'Urden",
        'image': "https://en.wikipedia.org/wiki/Drizzt_Do%27Urden#/media/File:Drizzt.png",  # noqa:E501
    },
}


def get_image(inputs):
    '''Get the image of a given character in the c_map'''

    try:
        return c_map[inputs.character.lower()]['image']
    except Exception:
        return None


def get_name(inputs):
    '''Get the name of a given character in the c_map'''

    try:
        return c_map[inputs.character.lower()]['name']
    except Exception:
        return inputs.character


def is_request_valid(request):
    '''Validate the request token with the expected values'''

    token = request.form['token'] == os.environ['SLACK_DND_VTOKEN']
    team_id = request.form['team_id'] == os.environ['SLACK_DND_TEAM_ID']

    return token and team_id


def parse_command(request):
    '''Parse the message as a command.'''

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--character',
        action='store',
    )
    parser.add_argument(
        '-e',
        '--emotion',
        action='store',
        default='',
    )
    parser.add_argument(
        '-H',
        '--how',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '-m',
        '--message',
        action='store',
        default='',
    )
    parser.add_argument(
        '-r',
        '--roll',
        action='store',
        default=None,
    )

    # This sucks:
    # The characters coming from different Slack clients can be unicode or not
    # In our situatio, iOS sends unicode quotes (at the very least) which
    # shlex chokes on.
    # Found this in stackoverflow which basically is a translation table from
    # silly unicode characters to associated ascii characters.
    # This list will need to be expanded over time if we find more unicode
    # characters that mess things up.
    # We can use `zappa tail` to check the traceback and see what's messing up
    # ...which I might leave the print statements here to facilitate easier
    # debugging
    transl_table = dict(
        [(ord(x), ord(y)) for x, y in zip(u"‘’´“”–-",  u"'''\"\"--")]
    )
    try:
        url_decoded = urllib.parse.unquote(request.form['text'])
        html_decoded = html.unescape(url_decoded)
        fixed_str = html_decoded.translate(transl_table)
        shlexd = shlex.split(fixed_str)
        args = parser.parse_args(shlexd)
    except Exception as e:
        print(f'Fixed String: {fixed_str}')
        print(str(e))
        abort(400)

    return args


def generate_accessory(inputs):
    '''Generate the Block accessory for character images.

    If a character is provided that has no image, set to None.
    '''

    accessory = {
        "type": "image",
        "image_url": get_image(inputs),
        "alt_text": "Characte Image"
    }
    if accessory['image_url'] is None:
        accessory = None

    return accessory


def generate_text(user, inputs):
    '''Generate the text to be sent to Slack.'''

    if inputs.how:
        hlp = (
            "/char -c [character name]\n"
            "If you'd like to add an emotion or action: -e '[emotion|action]'\n"  # noqa:E501
            "If you'd like to show what the characer says: -m \"[text]\"\n"
            "If you want to roll dice as well: -r \"[roll]\"\n"
        )
        return "{}".format(hlp)

    # Special mode checks go here if you want to do something special.
    if inputs.roll:
        result = f'{inputs.message}\n\n{str(roll(inputs.roll))}'
        return "*{} ...{} (from {})*\n{}".format(
                    get_name(inputs),
                    inputs.emotion,
                    user,
                    result
                )
    else:
        return "*{} ...{} (from {})*\n{}".format(
                    get_name(inputs),
                    inputs.emotion,
                    user,
                    inputs.message
                )


def build_data(channel, text, accessory):
    '''Build the data for the Slack message.'''

    data = {
        "channel": channel,
        "response_type": response_type,
        # This is to help notifications show text
        "text": text,
        "blocks": [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                },
            },
            {
                "type": "divider"
            }
        ]
    }

    # Add the image accessory if we found one
    if accessory:
        data['blocks'][1]['accessory'] = accessory

    return data


def post_to_slack(response_url, data):
    '''Send an HTTP POST to Slack with our message.'''

    requests.post(
        response_url,
        headers={'content-type': 'application/json'},
        data=json.dumps(data)
    )


def generate_message(request):
    '''Generate the message to send to Slack'''

    if not is_request_valid(request):
        abort(400)

    channel = request.form['channel_id']
    response_url = request.form['response_url']
    user = request.form['user_name']

    # Parse the command to get inputs
    inputs = parse_command(request)

    # If we don't have an image, don't include it in the accessory or the
    # POST to Slack will be invalid and fail.
    accessory = generate_accessory(inputs)

    # Generate message text.
    text = generate_text(user, inputs)

    # POST data to Slack using a Block (made using Block Builder)
    data = build_data(channel, text, accessory)

    # Make the POST to Slack for the created message
    # We do this instead of returning the message so we can prevent
    # the initial slash command from also showing up and duplicating our
    # message.
    post_to_slack(response_url, data)

    # Return an empty string so nothing gets posted to Slack
    return ""


# Important Character App Routes
# Each one of these is a command we can use in Slack with `/foo`


@app.route('/char', methods=['POST'])
def char():
    return generate_message(request)
