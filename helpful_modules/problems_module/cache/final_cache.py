from . import *

"Mainly used for backwards compatibility"

from .appeals_related_cache import AppealsRelatedCache
from ..errors import BGSaveNotSupportedOnSQLException
import typing
# TODO: make the initialize_sql_table
class MathProblemCache(AppealsRelatedCache):
    pass