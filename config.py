import os
basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

DAILY_NOTIFY_CHANNEL = os.environ['DAILY_NOTIFY_CHANNEL']
BOT_ID = os.environ['BOT_ID']
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']