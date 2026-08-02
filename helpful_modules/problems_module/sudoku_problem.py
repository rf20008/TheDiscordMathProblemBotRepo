# step 1: generate a random sudoku (i'm stuck on this part)
# there could be an api to do this, but i want to do that
# until the sudoku is minimal: (which means that if i remove any clue, it has multiple solutions; although this might call solve() a lot of times)
# randomly shuffle the list of clues. Go through that shuffled list: make a copy of the board, solve the copy and check if it has multiple solutions: if so, go onto the next one
# and if i get to the end the sudoku is minimal, otherwise go back to the beginning
# and then this is the board of my sudoku problem. the rest can be done with the FixedAnswerProblem constructor (I think)
# i think i'll have to defer any interaction at the beginning because i'm going to call solve() a lot of times and solve() is slow
# I might use heuristics because naïve backtracking is pretty slow 1) go to the cell with the least solutions instead of the next cell
# in the order and 2) immediately check numbers that don't work
# and 3) optimize the SudokuBoard so that it uses bitmasks so i can remove a constant factor
from helpful_modules.problems_module.auto_checkable_problem import AutoGradeableProblem


class SudokuProblem(AutoGradeableProblem):
    pass