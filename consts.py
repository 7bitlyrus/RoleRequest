ABOUT_URL = 'https://github.com/7bitlyrus/RoleRequest'
ABOUT_ISSUE_TRACKER = ABOUT_URL + '/issues'
ABOUT_TITLE = 'RoleRequest by 7bitlyrus'
ABOUT_DESCRIPTION = 'A simple role self-management bot for Discord.'

GIT_REPO_URL = 'https://github.com/7bitlyrus/RoleRequest'
GIT_COMMIT_BASE = GIT_REPO_URL + '/commit/'
GIT_COMPARE_BASE = GIT_REPO_URL + '/compare/'

LIMITED_RATELIMIT_SCORE_MAX = 21
LIMITED_RATELIMIT_SCORES = {
    'pending': 3,
    'cancelled': 5,
    'denied': 7
}

EMBED_LENGTH_LIMITS = {
    'overall': 6000,
    'description': 2048,
    'field_values': 1024
}

GIT_REPO_REGEX = r'(?:https?://)?(?:\w+@)?([^:/\s]+)[:|/]([^/\s]+)/([^/.\s]+)(?:.git)?'