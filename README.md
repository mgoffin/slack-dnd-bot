# slack-dnd-bot

This is a small Slack Bot for talking "in character".

# BEFORE YOU READ FURTHER

This is a bot I created for our own personal D&D game. We use Slack to schedule sessions, talk about the campaign, and sometimes talk "in character" between sessions to move the story along if we wish.

That being said, the character names in the dnd-bot.py file *COULD BE SPOILERS*. Review it at your own risk.

# How does the bot work?

This bot allows you to talk "in character" in a Slack channel. Some examples:

```
> /char -c Drizzt -m "Hello, world..."
> /char -c Drizzt -e "Excitedly" -m "Hello, world!"
> /char -c Drizzt -r "1d20"
```

You can also roll dice! It uses `d20` so see their readthedocs for syntax.
```
> /char -c Drizzt -e "Defiantly" -m "So be it!" -r "1d20"
```

In the file is a `c_map` dictionary which allows you to define any (N)PC you wish and a custom Display Name and image to show up in the Slack message.

## How to deploy

If you are new to testing and setting up a bot for Slack slash commands, this site has a wonderful writeup:

https://renzolucioni.com/serverless-slash-commands-with-python/

To get this running, simply replace their Python code with dnd-bot.py.
*NOTE*: You will need to modify the `c_map` in dnd-bot.py to reflect your own characters and NPCs.

Also, they reference some environment variables in the code. Due to conflicts with other bots, the code uses these environment variables:

* `SLACK_DND_VTOKEN`
* `SLACK_DND_TEAM_ID`

# Contributing

I would love contributions to make this bot better! Please submit an Issue and let me know what you'd like to see. Even better, once we agree on what should be added, please write it and submit a PR!

## Stuff I thought about

* Adding a spell lookup command, but since a lot of spells aren't publicly available, I felt it wasn't as useful as it could be.
* Additional command features to express something else about the character speaking, how they are speaking, etc.

# TODO

* Add typing to dnd-boy.py to ensure code clarity and conformity.
* Add example images so it's easier to see what things look like in Slack.
