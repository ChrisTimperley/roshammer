__all__ = ('get_test_type_database',)

import os

from roswire.definitions import FormatDatabase, TypeDatabase

DIR_TEST = os.path.dirname(__file__)
FN_DB_MAVROS = os.path.join(DIR_TEST, 'format-databases/mavros.formats.yml')
FORMAT_DB_MAVROS: FormatDatabase = FormatDatabase.load(FN_DB_MAVROS)
TYPE_DB_MAVROS: TypeDatabase = TypeDatabase.build(FORMAT_DB_MAVROS)


def get_test_type_database() -> TypeDatabase:
    return TYPE_DB_MAVROS
