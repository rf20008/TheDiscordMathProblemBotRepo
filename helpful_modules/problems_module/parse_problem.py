"""
The Discord Math Problem Bot Repo - DictConvertible
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

from .base_problem import BaseProblem
from .linear_algebra_problem import LinearAlgebraProblem
from .computational_problem import ComputationalProblem
import orjson
# TODO: When there are new problem types, this must handle it
def convert_dict_to_problem(data: dict, cache= None):
    if not isinstance(data, dict):
        raise TypeError("data is not a dict")
    if "type" not in data["extra_stuff"].keys():
        raise ValueError(f"data {data} doesn't have a type")
    match data["extra_stuff"]["type"]:
        case "BaseProblem": return BaseProblem.from_dict(data, cache)
        case "ComputationalProblem": return ComputationalProblem.from_dict(data, cache)
        case "LinearAlgebraProblem": return LinearAlgebraProblem.from_dict(data, cache)
        case _:
            raise ValueError("Type is mal-formed")
def convert_row_to_problem(row: dict, cache = None):
    if not isinstance(row, dict):
        raise TypeError("row is not a dict")
    try:
        extra_stuff = orjson.loads(row["extra_stuff"].replace("'", '"'))
    except orjson.JSONDecodeError:
        print(row["extra_stuff"])
        raise
    if "type" not in extra_stuff.keys():
        raise ValueError(f"row {row} doesn't have a type")
    match extra_stuff["type"]:
        case "BaseProblem": return BaseProblem.from_row(row, cache)
        case "ComputationalProblem": return ComputationalProblem.from_row(row, cache)
        case "LinearAlgebraProblem": return LinearAlgebraProblem.from_row(row, cache)
        case _:
            raise ValueError(f"The row {row} is mal-formed")