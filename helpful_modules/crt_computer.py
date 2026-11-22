"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of TheDiscordMathProblemBotRepo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

from math import gcd

import more_itertools

from helpful_modules import threads_or_useful_funcs


class ChineseRemainderTheoremComputer:
    def __init__(self, remainders: list[int], moduli: list[int]):
        self.remainders = remainders
        self.moduli = moduli
        self._validate()

    def _validate(self) -> None:
        if not isinstance(self.remainders, list):
            raise TypeError("Remainders is not a list")
        if not isinstance(self.moduli, list):
            raise TypeError("Moduli is not a list")
        if not all(isinstance(remainder, int) for remainder in self.remainders):
            raise TypeError("Remainders contains non-integer values")
        if not all(isinstance(moduli, int) for moduli in self.moduli):
            raise TypeError("Moduli contains non-integer values")
        if len(self.remainders) != len(self.moduli):
            raise ValueError(
                "The length of the remainders does not equal the length of the moduli!"
            )
        for a, b in more_itertools.distinct_combinations(self.moduli, 2):
            ABP = gcd(a, b)
            if ABP != 1:
                raise ValueError(
                    f"{a} and {b} are 2 of the moduli, but they have gcd({a}, {b}) = {ABP} != 1"
                )
        for i, (remainder, modulus) in enumerate(zip(self.remainders, self.moduli)):
            if modulus <= 0:
                raise ValueError(f"In congruence #{i+1}, the modulus {modulus} is nonpositive")
            if not modulus > remainder >= 0:
                raise ValueError(f"For congruence #{i+1}, the remainder {remainder} is not in the range [0, {modulus})")

    def compute(self, revalidate: bool=True):
        """Compute the CRT
        Algorithm credits to my brother

        revalidate: bool
        Whether to revalidate the conditions of the CRT being defined"""
        if revalidate:
            self._validate()
        product = 1
        for i in range(len(self.moduli)):
            product *= self.moduli[i]
        su = 0
        for i in range(len(self.moduli)):
            num = product // self.moduli[i]
            # compute the multiplicative number of product/b_i mod b_i
            return_val = pow(num, -1, self.moduli[i])
            mult_inv = return_val
            su += num * mult_inv * self.remainders[i]
            su %= product
        return su % product
