# RoleRequest
A simple role self-management bot for Discord. 

## Getting Started
* Clone the git repository 
* `pip install -r requirements.txt`
* Create a `config.py` file with the following format:
```py
# Your Discord bot token
token = '' 

# Emotes to use for approving/denying limited role requests
greenTick = 'greenTick:1234567890'
redTick = 'redTick:1234567890'
```
* `python bot.py`

## Types of roles
* *Open* - Roles that can be freely joined and left by users
* *Limited* - Roles that require moderator approval to join, initiated by the join command