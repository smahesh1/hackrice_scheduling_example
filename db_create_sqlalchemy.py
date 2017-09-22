#!starterbot/bin/python
from migrate.versioning import api
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import os
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

engine = create_engine(SQLALCHEMY_DATABASE_URI)
if not database_exists(engine.url):
    create_database(engine.url)

print(database_exists(engine.url))

if not os.path.exists(SQLALCHEMY_MIGRATE_REPO):
    api.create(SQLALCHEMY_MIGRATE_REPO, 'database repository')
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
else:
    api.version_control(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, api.version(SQLALCHEMY_MIGRATE_REPO))