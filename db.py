"""
gRunner's database module.
Some techniques have been omitted because of limitations of peewee.
Store like this:
    https://docs.peewee-orm.com/en/latest/peewee/quickstart.html#storing-data
"""

import peewee as p

from globals import Global

_db = p.SqliteDatabase(Global.DB)


class DBrunner(p.Model):
    class Meta:
        database = _db


class Application(DBrunner):
    path = p.CharField(primary_key=True)
    readable_name = p.CharField()
    opened_count = p.IntegerField()
    last_opened = p.TimestampField(resolution=6, utc=True)
    first_opened = p.TimestampField(resolution=6, utc=True)


class UserSession(DBrunner):
    # NOTE:
    #  path should have been a composite foreign key w/ time_stated, but peewee
    #  decided not to implement this in their library.
    path = p.CharField(null=False)
    time_started = p.TimestampField(resolution=6, utc=True, null=False)
    time_ended = p.TimestampField(resolution=6, utc=True, null=True)

    class Meta:
        primary_key = p.CompositeKey('path', 'time_started')


class ApplicationSession(DBrunner):
    # NOTE:
    #  path, time_started, & heartbeat should have been a composite foreign key, but peewee
    #  decided not to implement this in their library.
    path = p.CharField(null=False)
    time_started = p.TimestampField(resolution=6, utc=True, null=False)
    heartbeat = p.TimestampField(resolution=6, utc=True, null=False)
    total_memory_usage = p.IntegerField(null=False)
    process_count = p.IntegerField(null=False)

    class Meta:
        primary_key = p.CompositeKey('path', 'time_started', 'heartbeat')


_db.create_tables([Application, UserSession, ApplicationSession])
