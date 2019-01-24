import pytz


def datetime_to_local(dt, timezone):
    local_tz = pytz.timezone(timezone)
    dt = dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(dt).replace(tzinfo=None)
