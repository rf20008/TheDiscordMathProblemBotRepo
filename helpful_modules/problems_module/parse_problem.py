"""You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - ParseProblem

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import pickle

import orjson

from .base_problem import FixedAnswerProblem
from .computational_problem import ComputationalProblem
from .errors import FormatException
from .linear_algebra_problem import LinearAlgebraProblem

class_map = {
    "FixedAnswerProblem": FixedAnswerProblem,
    "ComputationalProblem": ComputationalProblem,
    "LinearAlgebraProblem": LinearAlgebraProblem,
}
# TODO: When there are new problem types, this must handle it
def convert_to_problem(data: dict, load_strat: str, cache=None):
    if not isinstance(data, dict):
        raise TypeError("row is not a dict")
    extra_stuff = data.get("extra_stuff", "{}")
    if isinstance(extra_stuff, str):
        try:
            extra_stuff = orjson.loads(extra_stuff.replace("'", '"'))
        except orjson.JSONDecodeError as err:
            raise FormatException(
                f"The extra stuff, which is {extra_stuff} is not valid json"
            ) from err
    data["voters"] = pickle.loads(data["voters"])
    data["solvers"] = pickle.loads(data["solvers"])
    data["answers"] = pickle.loads(data["answers"])
    if "type" not in extra_stuff.keys():
        raise ValueError(f"row {data} doesn't have a Problem type")
    try:
        prob_type = class_map[extra_stuff.get("type")]
    except KeyError:
        raise ValueError(f"Unknown problem type: {extra_stuff.get('type')}")
    return getattr(prob_type, load_strat)(data, cache)

def convert_dict_to_problem(data: dict, cache=None):
    return convert_to_problem(data, cache=cache, load_strat="from_dict")
def convert_row_to_problem(row: dict, cache=None):
    return convert_to_problem(row, cache=cache, load_strat="from_row")