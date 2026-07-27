# -*- coding:utf-8 -*-

from api.extensions import celery

# celery -A celery_worker.celery worker -l DEBUG -E -Q xxxx

# Break the circular import api.tasks.cmdb -> api.lib.cmdb.ci -> api.tasks.cmdb
# (the latter does `from api.tasks.cmdb import ci_cache` at module level).
# Loading api.lib.cmdb.ci first lets api.tasks.cmdb fully initialize when it
# is pulled in from there; the legacy flask worker got this ordering for free
# via create_app(). Also import the remaining task modules so that all queues
# (one_cmdb_async / acl_async / common_setting_async / beat_tasks) have their
# tasks registered, mirroring what create_app() imported on the flask side.
import api.lib.cmdb.ci  # noqa
import api.lib.common_setting.employee  # noqa

# Load beat schedules from all modules
from api.tasks.cmdb import CMDB_BEAT_SCHEDULE  # noqa

celery.conf.beat_schedule = celery.conf.get('beat_schedule', {})
celery.conf.beat_schedule.update(CMDB_BEAT_SCHEDULE)
