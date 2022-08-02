import re
from enum import Enum
import json
from typing import Tuple

from app.db import with_session
from logic.metastore import get_table_by_id


class SamplesError(Exception):
    pass


@with_session
def make_samples_query(
    table_id,
    limit,
    partition=None,
    where: Tuple[str, str, str] = None,
    order_by=None,
    order_by_asc=True,
    session=None,
):
    table = get_table_by_id(table_id, session=session)
    information = table.information
    columns = table.columns
    column_type_by_name = {
        column.name: get_column_type_from_string(column.type) for column in columns
    }
    query_filters = []

    partitions = []
    if information:
        partitions = json.loads(information.to_dict().get("latest_partitions") or "[]")

    if partition is None:
        partition = next(iter(reversed(partitions)), None)
    elif not len(partitions) or partition not in partitions:
        raise SamplesError(f"Invalid partition {partition}")

    if partition:  # latest_partitions is like dt=2015-01-01/column1=val1
        for column_filter in partition.split("/"):
            column_name, column_val = column_filter.split("=")
            column_type = column_type_by_name.get(column_name)
            column_quote = ""
            if column_type == QuerybookColumnType.String:
                column_quote = "'"

            query_filters.append(
                f"{column_name}={column_quote}{column_val}{column_quote}"
            )

    if where is not None:
        column_name, filter_op, filter_val = where
        if column_name not in column_type_by_name:
            raise SamplesError(f"Invalid filter column {column_name}")
        column_type = column_type_by_name[column_name]

        if filter_op not in COMPARSION_OP:
            raise SamplesError(f"Invalid filter op {filter_op}")

        if filter_op in ["=", "!=", "LIKE"]:
            if column_type == QuerybookColumnType.Number:
                if not filter_val or not filter_val.isnumeric():
                    raise SamplesError(f"Invalid numeric filter value {filter_val}")
            elif column_type == QuerybookColumnType.Boolean:
                if filter_val not in ["true", "false"]:
                    raise SamplesError(f"Invalid boolean filter value {filter_val}")
            else:  # column_type == QuerybookColumnType.String
                filter_val = f"'{json.dumps(filter_val)[1:-1]}'"
        else:
            filter_val = ""

        query_filters.append(f"{column_name} {filter_op} {filter_val}")

    query_filter_str = (
        f'WHERE\n{" AND ".join(query_filters)}' if len(query_filters) else ""
    )


    order_by_str = ""
    if order_by is not None:
        if order_by not in column_type_by_name:
            raise SamplesError(f"Invalid order by {order_by}")
        order_by_str = f'ORDER BY {order_by} {"ASC" if order_by_asc else "DESC"}'

    full_name = f"{table.data_schema.name}.{table.name}"
    return """
SELECT
    *
FROM {}
{}
{}
LIMIT {}""".format(
        full_name, query_filter_str, order_by_str, limit
    )


COMPARSION_OP = ["=", "!=", "LIKE", "IS NULL", "IS NOT NULL"]


class QuerybookColumnType(Enum):
    String = "string"
    Number = "number"
    Boolean = "boolean"

    # For composite types
    Composite = "composite"
    Unknown = "unknown"


common_sql_types = {
    "boolean": QuerybookColumnType.Boolean,
    # Integers
    "int": QuerybookColumnType.Number,
    "integer": QuerybookColumnType.Number,
    "tinyint": QuerybookColumnType.Number,
    "smallint": QuerybookColumnType.Number,
    "mediumint": QuerybookColumnType.Number,
    "bigint": QuerybookColumnType.Number,
    # Floats
    "real": QuerybookColumnType.Number,
    "numeric": QuerybookColumnType.Number,
    "decimal": QuerybookColumnType.Number,
    "double": QuerybookColumnType.Number,
    # Time
    "date": QuerybookColumnType.String,
    "datetime": QuerybookColumnType.String,
    "time": QuerybookColumnType.String,
    "timestamp": QuerybookColumnType.String,
    "interval": QuerybookColumnType.String,
    # String
    "string": QuerybookColumnType.String,
    "char": QuerybookColumnType.String,
    "varchar": QuerybookColumnType.String,
    "text": QuerybookColumnType.String,
    "tinytext": QuerybookColumnType.String,
    "mediumtext": QuerybookColumnType.String,
    "longtext": QuerybookColumnType.String,
    "blob": QuerybookColumnType.String,
    "longblob": QuerybookColumnType.String,
    "varbinary": QuerybookColumnType.String,
    "json": QuerybookColumnType.Composite,
    "array": QuerybookColumnType.Composite,
    "map": QuerybookColumnType.Composite,
    "row": QuerybookColumnType.Composite,
    "uniontype": QuerybookColumnType.Composite,
    "struct": QuerybookColumnType.Composite,
}


def get_column_type_from_string(raw_column: str) -> QuerybookColumnType:
    """Converts column type from different language into a
       more understandable format

    Arguments:
        raw_column {str} -- The column type string, can be any column type defined in
        presto, hive, mysql, etc...

    Returns:
        QuerybookColumnType -- Column type that's understood by Querybook
    """

    # Extract the start of the raw_column
    match = re.match(r"^([a-zA-Z]+)", raw_column)
    first_word = match[1].lower() if match is not None else ""

    return (
        common_sql_types[first_word]
        if first_word in common_sql_types
        else QuerybookColumnType.Unknown
    )
