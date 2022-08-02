import csv
from io import StringIO
import sys
from typing import List
from datetime import datetime


from app.db import with_session
from models.result_store import KeyValueStore

# HACK: https://stackoverflow.com/questions/15063936/csv-error-field-larger-than-field-limit-131072
csv.field_size_limit(sys.maxsize)


@with_session
def create_key_value_store(key, value, commit=True, session=None):
    return KeyValueStore.create(
        {"key": key, "value": value}, commit=commit, session=session
    )


@with_session
def update_key_value_store(key, value, commit=True, session=None):  # csv
    kvs = get_key_value_store(key, session=session)

    kvs.value = value
    kvs.updated_at = datetime.utcnow()

    if commit:
        session.commit()

    else:
        session.flush()
    kvs.id
    return kvs


@with_session
def upsert_key_value_store(key, value, commit=True, session=None):
    if kvp := get_key_value_store(key, session=session):
        return update_key_value_store(key, value, commit, session=session)
    else:
        return create_key_value_store(key, value, commit, session=session)


@with_session
def get_key_value_store(key, session=None):
    return KeyValueStore.get(session=session, key=key)


@with_session
def delete_key_value_store(key, commit=True, session=None):
    if item := get_key_value_store(key=key, session=session):
        session.delete(item)
        if commit:
            session.commit()


def string_to_csv(raw_csv_str: str) -> List[List[str]]:
    # Remove NULL byte to make sure csv conversion works
    raw_csv_str = raw_csv_str.replace("\x00", "")
    result = []

    if raw_csv_str != "":
        raw_results = StringIO(raw_csv_str)
        csv_reader = csv.reader(raw_results, delimiter=",")
        result = list(csv_reader)
    return result
