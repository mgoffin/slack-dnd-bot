import json
import os
import requests

from flask import abort, Flask, request


app = Flask(__name__)

# Set response type
response_type = "in_channel"  # ephemeral

# Character lookup for anyone with a real name and image.
# Each key/value pair should be in the form of:
# 'slash_cmd': {'name': 'Display Name', 'image': 'url to image to display'}
c_map = {
    'uhl': {
        'name': "Uhl",
        'image': "https://s3.amazonaws.com/gt7sp-prod/decal/44/03/79/6917551022387790344_1.png",  # noqa:E501
    },
    'jade': {
        'name': "Jade",
        'image': "https://orderofsyncletica.files.wordpress.com/2014/02/assassin.jpg?w=768&h=480",  # noqa:E501
    },
    'elijah': {
        'name': "Elijah",
        'image': "https://media-waterdeep.cursecdn.com/avatars/thumbnails/7/267/1000/1000/636284743262192738.jpeg",  # noqa:E501
    },
    'hal': {
        'name': "Hal",
        'image': "http://isandir.com/wp-content/uploads/Damen.png",  # noqa:E501
    },
    'rvr': {
        'name': "Rudolph",
        'image': "https://vignette.wikia.nocookie.net/castlevania/images/0/0a/Abraham_Van_Helsing_-_Anthony_Hopkins_-_01.jpg/revision/latest?cb=20141205103112",  # noqa:E501
    },
    'nikolaj': {
        'name': "Nikolaj",
        'image': "https://vignette.wikia.nocookie.net/the-cloaks/images/3/36/Berrian_Lackman_Portrait_zpsk530fyq4.png/revision/latest?cb=20170709093418",  # noqa:E501
    },
    'strahd': {
        'name': "Lord Strahd",
        'image': "https://pbs.twimg.com/profile_images/790396156224217088/jB2kFMlM_400x400.jpg",  # noqa:E501
    },
    'ireena': {
        'name': "Ireena",
        'image': "https://vignette.wikia.nocookie.net/sundnd/images/6/6e/Ireena.png/revision/latest?cb=20171102201638",  # noqa:E501
    },
    'ismark': {
        'name': "Ismark",
        'image': "https://vignette.wikia.nocookie.net/mnmh/images/3/36/Ismark_Lesser.jpg/revision/latest?cb=20190118154038",  # noqa:E501
    },
    'hakkon': {
        'name': "Brother Hakkon",
        'image': "https://cdn.webshopapp.com/shops/32318/files/254957012/600x600x2/medieval-chaperon-walt-black.jpg",  # noqa:E501
    },
    'izek': {
        'name': "Izek",
        'image': "https://i2-prod.mirror.co.uk/incoming/article429356.ece/ALTERNATES/s615b/nikolai-valuev-pic-getty-images-45880687.jpg",  # noqa:E501
    },
    'geri': {
        'name': "Geri",
        'image': "https://mcishop.azureedge.net/mciassets/w_3_0034933_chainmail-shirt.png",  # noqa:E501
    }
}


def get_image(character):
    '''Get the image of a given character in the c_map'''

    try:
        return c_map[character.lower()]['image']
    except Exception:
        return None


def get_name(character):
    '''Get the name of a given character in the c_map'''

    try:
        return c_map[character.lower()]['name']
    except Exception:
        return character


def is_request_valid(request):
    '''Validate the request token with the expected values'''

    token = request.form['token'] == os.environ['SLACK_DND_VTOKEN']
    team_id = request.form['team_id'] == os.environ['SLACK_DND_TEAM_ID']

    return token and team_id


def parse_gm_command(request):
    '''Parse a message as a GM command.'''

    msg_l = request.form['text'].split('|')
    if len(msg_l) == 3:
        character = msg_l[0].strip()
        mode = " [{}]".format(msg_l[1].strip())
        msg = msg_l[2].strip()
    elif len(msg_l) == 2:
        character = msg_l[0].strip()
        mode = ""
        msg = msg_l[1].strip()

    return character, mode, msg


def parse_character_command(request):
    '''Parse a message as a Player command.'''

    msg_l = request.form['text'].split('|')
    character = request.form['command'].replace("/", "")
    if len(msg_l) == 2:
        mode = " [{}] ".format(msg_l[0].strip())
        msg = msg_l[1].strip()
    else:
        mode = ""
        msg = msg_l[0]

    return character, mode, msg


def generate_accessory(character):
    '''Generate the Block accessory for character images.

    If a character is provided that has no image, set to None.
    '''

    accessory = {
        "type": "image",
        "image_url": get_image(character),
        "alt_text": "Characte Image"
    }
    if accessory['image_url'] is None:
        accessory = None

    return accessory


def generate_text(character, mode, user, msg):
    '''Generate the text to be sent to Slack.'''

    return "*{} Says...{} (from {})*\n{}".format(
            get_name(character), mode, user, msg)


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

    command = request.form['command']
    channel = request.form['channel_id']
    response_url = request.form['response_url']
    user = request.form['user_name']

    # GM Command is more flexible in the form of `/gm name | message`
    if command == "/gm":
        character, mode, msg = parse_gm_command(request)
    else:
        character, mode, msg = parse_character_command(request)

    # If we don't have an image, don't include it in the accessory or the
    # POST to Slack will be invalid and fail.
    accessory = generate_accessory(character)

    # Generate message text.
    text = generate_text(character, mode, user, msg)

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


@app.route('/uhl', methods=['POST'])
def uhl():
    return generate_message(request)


@app.route('/jade', methods=['POST'])
def jade():
    return generate_message(request)


@app.route('/elijah', methods=['POST'])
def elijah():
    return generate_message(request)


@app.route('/hal', methods=['POST'])
def hal():
    return generate_message(request)


@app.route('/rvr', methods=['POST'])
def rvr():
    return generate_message(request)


@app.route('/nikolaj', methods=['POST'])
def nikolaj():
    return generate_message(request)


@app.route('/gm', methods=['POST'])
def gm():
    return generate_message(request)


@app.route('/strahd', methods=['POST'])
def strahd():
    return generate_message(request)
