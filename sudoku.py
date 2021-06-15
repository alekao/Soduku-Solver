"""CSC111 Winter 2021 Project: Sudoku Solver

This module contains the Sudoku solvers implemented using the Graph data type.
In particular, the Sudoku class and Vertex class are parent classes of ClassicSudoku
, KillerSudoku and _ClaVertex, _KilVertex, as they contain the functions shared by
these two Sudoku variants.

Two additional dataclasses are defined for KillerSudoku and _KilVertex: Cage and IndirectCage.
Cage contains information about a cage in a Killer Sudoku with coordinates, and IndirectCage
contains information about an indirect cage with vertices.

The sudoku_dataset function at the end generates dataset for a specific type of Sudoku,
to use this function, comment the self.generate(filename) line in the __init__ method
of that Sudoku variant and uncomment all other codes in it.

Copyright and Usage Information
===============================

This file is Copyright (c) 2021 Raymond Liu
"""
from __future__ import annotations
from typing import Optional, Callable, Union
from dataclasses import dataclass
import copy
import random
import pickle
import pprint


class Sudoku:
    """A Sudoku puzzle represented using a graph.

    Private attributes:
        - _entries: a dictionary that maps the coordinate of each entry to the vertex
        representing that entry; (1, 1) represents the top-left corner of the grid,
        (1, 2) represents the entry below the top-left entry, etc.
    """
    _entries: dict[tuple[int, int], _Vertex]

    def solve(self) -> bool:
        """Return whether the puzzle is solvable or not. If it is solvable, all the entries
        will be mutated to the solution. If it is unsolvable, then do no changes to the
        entries and return False.
        """
        original = copy.deepcopy(self._entries)
        state_copies = []

        entry, unique_value = self._search()

        while entry is not None:
            if unique_value is not None:
                next_assign = entry.assign(unique_value)

            elif len(entry.valid_values) == 0:
                # print('dead end')
                if len(state_copies) == 0:
                    self._entries = original
                    return False
                state_copy, prev_choice, coordinate = state_copies.pop()
                self._entries = state_copy
                next_assign = self._entries[coordinate]
                next_assign.valid_values.discard(prev_choice)

            elif len(entry.valid_values) == 1:
                next_assign = entry.assign(next(iter(entry.valid_values)))

            else:
                # print('multiple choice')
                state_copy, prev_choice, coordinate = self._record_state(entry)
                state_copies.append((state_copy, prev_choice, coordinate))
                next_assign = entry.assign(prev_choice)

            if next_assign is not None:
                entry, unique_value = next_assign, None
            else:
                entry, unique_value = self._search()

        return True

    def _search(self) -> tuple[Optional[_Vertex], Optional[int]]:
        """If an entry has a unique value or only one valid value, return that entry and
        its (possibly None) unique value. If an entry has no valid value, meaning that
        the current solving process is wrong, return that entry.

        Otherwise, return the entry with the minimum number of valid_values.

        Return None if all entry already has a value -- the puzzle is solved.
        """
        min_valid_value = None
        num_filled = 0
        for coordinate in self._entries:
            entry = self._entries[coordinate]

            if entry.value is None:
                num_valid_values = len(entry.valid_values)
                unique_value = self._unique_valid_value(coordinate)

                if num_valid_values == 0:
                    return (entry, None)
                elif num_valid_values == 1 or unique_value is not None:
                    return (entry, unique_value)
                elif min_valid_value is None or \
                        num_valid_values < len(min_valid_value.valid_values):
                    min_valid_value = entry

            else:
                num_filled += 1

        if num_filled == 81:
            return (None, None)
        else:
            return (min_valid_value, None)

    def _unique_valid_value(self, coordinate: tuple[int, int]) -> Optional[int]:
        """Return the valid value of the entry at (x, y) that is not in the valid values
        of all of its row neighbours, all of its column neighbours, or all of its subgrid
        neighbours, if there is any; otherwise return None."""
        x, y = coordinate
        entry = self._entries[(x, y)]

        for value in entry.valid_values:
            if all(value not in self._entries[(i, y)].valid_values
                   for i in range(1, 10) if i != x):
                return value

            if all(value not in self._entries[(x, j)].valid_values
                   for j in range(1, 10) if j != y):
                return value

            subgrid = ((x - 1) // 3 * 3 + 1, (y - 1) // 3 * 3 + 1)
            if all(value not in self._entries[(k1, k2)].valid_values
                   for k1 in range(subgrid[0], subgrid[0] + 3)
                   for k2 in range(subgrid[1], subgrid[1] + 3)
                   if k1 != x or k2 != y):
                return value

        return None

    def _record_state(self, entry: _Vertex) -> \
            tuple[dict[tuple[int, int], _Vertex], int, tuple[int, int]]:
        """Return a deep copy of self._entries, a value in entry's valid_values, and
        the coordinate of that entry."""
        state_record = copy.deepcopy(self._entries)
        choice = next(iter(entry.valid_values))
        coordinate = None
        for key in self._entries:
            if self._entries[key] is entry:
                coordinate = key
        return state_record, choice, coordinate

    def generate_puzzle(self) -> dict[tuple[int, int], _Vertex]:
        """Generate a new solvable puzzle."""
        raise NotImplementedError

    def _fill_random_entries(self, num: int = 0) -> None:
        """Create a new puzzle by randomly filling values/creating cages."""
        raise NotImplementedError

    def generate(self, filename: str) -> None:
        """Take a random puzzle from the previously generated puzzle file and assign it
        to the current one."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear the puzzle to its initial state."""
        raise NotImplementedError

    def _connect_entries(self, x: int, y: int, vertex: Callable) -> None:
        """Create a new instance of _Vertex as a new entry for the puzzle,
        and create an edge between all previously created entries that are in
        the same row, column, and 3 x 3 subgrid with it.

        Preconditions:
            - 1 <= row <= 9
            - 1 <= col <= 9
        """
        new_entry = vertex()
        self._entries[(x, y)] = new_entry

        for k in range(1, x + 1):
            self._add_edge(k, y, new_entry)
        for k in range(1, y + 1):
            self._add_edge(x, k, new_entry)

        subgrid = ((x - 1) // 3 * 3 + 1, (y - 1) // 3 * 3 + 1)
        for k2 in range(subgrid[1], y):
            for k1 in range(subgrid[0], subgrid[0] + 3):
                self._add_edge(k1, k2, new_entry)

    def _add_edge(self, i: int, j: int, v: _Vertex) -> None:
        """Add an edge between the entry at (x, y) and the given entry.

        Preconditions:
            - 1 <= i <= 9 and 1 <= j <= 9
        """
        u = self._entries[(i, j)]
        if u is not v:
            v.neighbours.add(u)
            u.neighbours.add(v)

    def assign(self, x: int, y: int, value: int) -> None:
        """Assign the given value to the entry at (x, y) in the Sudoku puzzle.

        Preconditions:
            - 1 <= x <= 9 and 1 <= y <= 9 and 1 <= value <= 9
        """
        self._entries[(x, y)].assign(value)

    def get_entry(self, x: int, y: int) -> Optional[int]:
        """Return the value of the entry at coordinate (x, y).

        Preconditions:
            - 1 <= x <= 9 and 1 <= y <= 9
        """
        return self._entries[(x, y)].value

    def print_puzzle(self) -> None:
        """Print the current puzzle."""
        solution = []
        for i in range(1, 10):
            row = []
            for j in range(1, 10):
                value = self._entries[(j, i)].value
                if value is None:
                    row.append(0)
                else:
                    row.append(value)
            solution.append(row)

        pprint.pprint(solution)


class _Vertex:
    """An entry in a Sudoku game represented using a vertex.

    Representation Invariants:
        - self not in self.neighbours
        - all(self in neighbour.neighbours for neighbour in self.neighbours)

    Public attributes:
        - value: the current value of this entry in the Sudoku game. This value is
        by default None until it is filled.
        - neighbours: a set containing all entries in the Sudoku game that may be
        influenced by changes in this entry.
        - valid_values: a set containing all valid values that this entry can have
        without violating the rule of the game.
    """
    value: Optional[int]
    neighbours: set[_Vertex]
    valid_values: set[int]

    def __init__(self) -> None:
        """Initialize an entry."""
        self.value = None
        self.neighbours = set()
        self.valid_values = {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def assign(self, value: int) -> Optional[_Vertex]:
        """Assign the given value to this entry and mutate the valid values of all
        entries that it is related to."""
        raise NotImplementedError


class ClassicSudoku(Sudoku):
    """A classic Sudoku puzzle."""

    _entries: dict[tuple[int, int], _ClaVertex]

    def __init__(self) -> None:
        """Initialize a classic Sudoku puzzle by setting every entry(vertex) as
        empty."""
        # self._entries = {}

        # for y in range(1, 10):
        #     for x in range(1, 10):
        #         self._connect_entries(x, y, _ClaVertex)

        self.generate('classic_sudoku.pkl')

    def generate_puzzle(self) -> dict[tuple[int, int], _ClaVertex]:
        """Generate and return a new Sudoku puzzle.

        The puzzle will be generated by repeatedly filling 23 - 33 random entries in
        the puzzle until the puzzle is solvable.
        """
        self.clear()
        num_fill = random.randint(23, 33)
        self._fill_random_entries(num_fill)
        puzzle = copy.deepcopy(self._entries)

        while not self.solve():
            self.clear()
            self._fill_random_entries(num_fill)
            puzzle = copy.deepcopy(self._entries)

        self.clear()

        return puzzle

    def generate(self, filename: str) -> None:
        """Take a random puzzle from the previously generated puzzle file and assign
        it to self._entries."""
        with open(filename, 'rb') as file:
            self._entries = random.choice(pickle.load(file))

    def _fill_random_entries(self, num: int = 0) -> None:
        """Randomly fill <num> entries in the empty puzzle with random values."""
        entries = list(self._entries.values())
        i = 0

        while i < num:
            entry = random.choice(entries)
            if entry.value is None:
                if entry.valid_values == set():
                    return
                entry.assign(random.choice(list(entry.valid_values)))
                i += 1

    def clear(self) -> None:
        """Clear the value of all entries in the puzzle."""
        for entry in self._entries.values():
            entry.value, entry.valid_values = None, {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def change_entry(self, x: int, y: int, value: int) -> bool:
        """Return whether the entry at (x, y) can be changed/assigned to the given <value>.

        Preconditions:
            - 1 <= x <= 9 and 1 <= y <= 9
        """
        return self._entries[(x, y)].change(value)

    def clear_entry(self, x: int, y: int) -> None:
        """Clear the value of the entry at (x, y).

        Preconditions:
            - 1 <= x <= 9 and 1 <= y <= 9
        """
        self._entries[(x, y)].clear()


class _ClaVertex(_Vertex):
    """An entry in a classic Sudoku game represented using a vertex.

    Public attributes:
        - neighbours: a set containing all entries in the Sudoku game that relates to
        this entry. Namely, the entry that is on the same row, column, and 3 x 3 grid.
    """
    neighbours: set[_ClaVertex]

    def assign(self, value: int) -> Optional[_ClaVertex]:
        """Assign a value to this entry, and updating the valid values of
        all neighbours.

        If the number of valid values of an entry becomes 1 after this
        value assignment, return it. Otherwise, return None.

        Preconditions:
            - value in self.valid_values
        """
        self.value = value
        self.valid_values = set()

        next_assign = None
        for v in self.neighbours:
            if v.value is None:
                v.valid_values.discard(value)

                if len(v.valid_values) == 1:
                    next_assign = v

        return next_assign

    def change(self, value: int) -> bool:
        """Return whether this entry can be changed/assigned with the given <value>.

        If True, then change the entry's value and valid_values and mutate the valid_values
        of all its neighbours accordingly. Otherwise, do nothing and return False.
        """
        if any(u.value == value for u in self.neighbours if u.value is not None):
            return False

        if self.value is None:
            if value in self.valid_values:
                self.assign(value)
                return True
            else:
                return False

        for v in self.neighbours:
            if v.value is None:
                if all(self.value != u.value for u in v.neighbours if u is not self):
                    v.valid_values.add(self.value)
                v.valid_values.discard(value)
        self.value = value
        return True

    def clear(self) -> None:
        """Set the value of this entry to None and re-calculate the valid_values based on the
        values of its neighbours. In addition, mutate the valid_value of its neighbours"""
        if self.value is not None:
            self.valid_values = {1, 2, 3, 4, 5, 6, 7, 8, 9}

            for v in self.neighbours:
                if v.value is None:
                    if all(self.value != u.value for u in v.neighbours if u is not self):
                        v.valid_values.add(self.value)
                else:
                    self.valid_values.discard(v.value)
            self.value = None


class KillerSudoku(Sudoku):
    """A Killer Sudoku puzzle.

    Public attributes;
        - cages: a list of Cage instances, each representing a cage in the puzzle.
        Cage.sum is the expected sum of a cage, and Cage.coordinates contains the
        coordinates of all entries in a cage.

    Private attributes:
        - _entries: a dictionary that maps the coordinate of each entry to the vertex
        representing that entry.; (1, 1) represents the top-left corner of the grid,
        (1, 2) represents the entry below the top-left entry, etc
    """
    _entries: dict[tuple[int, int], _KilVertex]
    cages: list[Cage]

    def __init__(self) -> None:
        """Initialize a Killer Sudoku puzzle."""
        # self._entries = {}
        #
        # for y in range(1, 10):
        #     for x in range(1, 10):
        #         self._connect_entries(x, y, _KilVertex)
        #
        # self.cages = []
        self.generate('killer_sudoku.pkl')

    def generate_puzzle(self) -> list[Union[dict[tuple[int, int], _KilVertex], list[Cage]]]:
        """Generate and return a new Sudoku puzzle to store in a file as dataset.

        The puzzle will be generated by first creating random cages, then generating
        a classic Sudoku puzzle and solving it. Finally, obtain the cage sum by adding
        the value of the entries in that cage."""
        self._fill_random_entries()
        while sum(len(c.coordinates) for c in self.cages) != 81:
            print('creating cage')
            self.clear()
            self._fill_random_entries()

        classic_sudoku = ClassicSudoku()

        cla_puzzle = classic_sudoku.generate_puzzle()
        classic_sudoku._entries = cla_puzzle
        classic_sudoku.solve()

        for cage in self.cages:
            cage.sum = sum(classic_sudoku.get_entry(*coordinate) for coordinate in cage.coordinates)

        self._connect_cages()

        assert all(entry.valid_values != set() for entry in self._entries.values())

        entries = copy.deepcopy(self._entries)
        cages = copy.deepcopy(self.cages)

        self.clear()

        return [entries, cages]

    def _fill_random_entries(self, num: int = 0) -> None:
        """Randomly choose cages of size 2 - 7 to fill the Sudoku puzzle.

        When creating a cage, entry adjacent to the existing entries in the cage
        will be chosen while making sure that the entries that are not yet in a
        cage are connected.
        """
        no_cage = list(self._entries.keys())

        attempt = 0
        while len(no_cage) != 0:
            entries_in_cage = []

            # Pick a random length for the cage
            length = random.randint(2, min(7, len(no_cage)))
            while len(no_cage) - length == 1:
                length = random.randint(2, min(7, len(no_cage)))
            max_attempts = length * 5

            # Repeatedly pick adjacent entry of the existing cage while making sure that
            # the entries in no_cage are connected.
            num_attempt = 0
            while len(entries_in_cage) != length and num_attempt < max_attempts:
                if entries_in_cage == []:
                    new_entry = random.choice(no_cage)
                    entries_in_cage = [new_entry]
                else:
                    new_entry = random.choice(self._possible_adjacent(entries_in_cage, no_cage))
                    entries_in_cage.append(new_entry)

                no_cage.remove(new_entry)

                if len(no_cage) != 0 and not self._connected(no_cage[0], no_cage, set()):
                    removed = entries_in_cage.pop()
                    no_cage.append(removed)

                num_attempt += 1

            if num_attempt != max_attempts:
                self.cages.append(Cage(sum=0, coordinates=entries_in_cage))
            else:
                no_cage.extend(entries_in_cage)

            attempt += 1
            if attempt > 400:
                break

    def _connect_cages(self) -> None:
        """Mutate the entries in the puzzle so that they have the entries in
        the same cage and the cage sum.

        Then obtain the indirect cages by finding all implicit sums between cages.
        For instance, if two cages with cage sum 20, 15 are subsets of the first row,
        then the remaining entries in the first row must have a sum of 45 - 20 - 15 = 10.
        Thus an indirect cage with cage sum 10 is created for these entries.

        Finally, update the valid_values of all entries.
        """
        for cage in self.cages:
            for i1 in range(len(cage.coordinates)):
                entry1 = self._entries[cage.coordinates[i1]]
                entry1.cage_sum = cage.sum
                for i2 in range(i1):
                    entry2 = self._entries[cage.coordinates[i2]]
                    entry1.cage_entries.add(entry2)
                    entry2.cage_entries.add(entry1)

        for i in range(1, 10):
            basics = [{(i, j) for j in range(1, 10)},
                      {(j, i) for j in range(1, 10)},
                      {((i - 1) % 3 * 3 + 1 + k1, (i - 1) // 3 * 3 + 1 + k2)
                       for k1 in range(3) for k2 in range(3)}]
            sums = [45, 45, 45]

            for cage in self.cages:
                cage_entries = set(cage.coordinates)
                for k in range(len(basics)):
                    if cage_entries.issubset(basics[k]):
                        basics[k] = basics[k].difference(cage_entries)
                        sums[k] -= cage.sum

            for coords, cage_sum in zip(basics, sums):
                if len(coords) != 9 and len(coords) != 0:
                    for coord in coords:
                        self._entries[coord].indirect_cages.append(
                            IndirectCage(cage_sum, [self._entries[x] for x in coords]))

        for entry in self._entries.values():
            entry.update_valid_values()

    def _possible_adjacent(self, entries_in_cage: list[tuple[int, int]],
                           no_cage: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Return a list of coordinates that are adjacent to entries in <entries_in_cage>
        and are in no_cage."""
        possible_adjacents = []
        for coordinate in entries_in_cage:
            x, y = coordinate
            possible_adjacent = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
            for coord in possible_adjacent:
                if coord in no_cage:
                    possible_adjacents.append(coord)
        return possible_adjacents

    def _connected(self, coordinate: tuple[int, int], no_cage: list[tuple[int, int]],
                   visited: set[tuple[int, int]]) -> bool:
        """Return whether the entries in no_cage are connected or not."""
        x, y = coordinate
        valid_coords = []
        possible_adjacent = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
        for coord in possible_adjacent:
            if coord in no_cage and coord not in visited:
                visited.add(coord)
                valid_coords.append(coord)
        visited.add(coordinate)

        for coord in valid_coords:
            self._connected(coord, no_cage, visited)

        if len(visited) == len(no_cage):
            return True

        return False

    def generate(self, filename: str) -> None:
        """Take a random puzzle from the previously generated puzzle file and assign
        it to self._entries and self.cages."""
        with open(filename, 'rb') as file:
            entries_and_cages = random.choice(pickle.load(file))
            self._entries = entries_and_cages[0]
            self.cages = entries_and_cages[1]

    def clear(self) -> None:
        """Clear the value of all entries, all cage sum, and all direct and indirect
        cage in the puzzle."""
        for entry in self._entries.values():
            entry.value, entry.valid_values = None, {1, 2, 3, 4, 5, 6, 7, 8, 9}
            entry.cage_sum, entry.cage_entries, entry.indirect_cages = 0, set(), []

        self.cages = []


class _KilVertex(_Vertex):
    """An entry in a Sudoku game represented using a vertex.

    Public attributes:
        - neighbours: a set containing all entries in the Sudoku game that relates to
        this entry. Namely, the entry that is on the same row, column, and 3 x 3 grid.
        - cage_entries: a set of entries in the same cage.
        - cage_sum: the sum of the cage that this entry is in
        - indirect_cages: a list of instances of IndirectCage, each representing an
        indirect cage, where IndirectCage.sum is the sum of that cage, and
        IndirectCage.entries is the set of all entries in the indirect cage.
    """
    neighbours: set[_KilVertex]
    cage_entries: set[_KilVertex]
    cage_sum: int
    indirect_cages: list[IndirectCage]

    def __init__(self) -> None:
        """Initialize an entry for a Killer Sudoku puzzle."""
        super(_KilVertex, self).__init__()
        self.cage_entries = set()
        self.cage_sum = 0
        self.indirect_cages = []

    def assign(self, value: int) -> Optional[_Vertex]:
        """Assign the given value to this entry, and set its valid values to an empty set.
        Then mutate the valid values of all its neighbours, cage neighbours, and indirect cage
        neighbours.

        Return the entry with only one valid value after the mutation, if there is any, otherwise
        return None.

        Preconditions:
            - value in self.valid_values
        """
        self.value = value
        self.valid_values = set()

        next_assign = None
        for v in self.neighbours:
            if v.value is None:
                v.valid_values.discard(value)

                if len(v.valid_values) == 1:
                    next_assign = v

        result = self.update_valid_values()
        if result is not None:
            next_assign = result

        return next_assign

    def update_valid_values(self) -> Optional[_KilVertex]:
        """Update the valid values of this entry as well as all its cage neighbours
        and indirect cage neighbours.

        Return the entry with only one valid value after the mutation, if there is any, otherwise
        return None.
        """
        next_assign = None
        cages = list(self.cage_entries) + [self]
        result = self.update_cage_valid_values(cages, self.cage_sum)
        if result is not None:
            next_assign = result

        for indirect_cage in self.indirect_cages:
            result = self.update_cage_valid_values(indirect_cage.entries, indirect_cage.sum)
            if result is not None:
                next_assign = result

        return next_assign

    def update_cage_valid_values(self, cages: list[_KilVertex], cage_sum: int) \
            -> Optional[_KilVertex]:
        """Update the valid values of this entry and its cage neighbours.

        Return the entry with only one valid value after the mutation, if there is any, otherwise
        return None.
        """
        has_value = 0
        no_value = len(cages)
        while has_value != no_value:
            if cages[has_value].value is not None:
                has_value += 1
            else:
                cages[has_value], cages[no_value - 1] = cages[no_value - 1], cages[has_value]
                no_value -= 1

        if has_value != len(cages):
            known_values = [cages[j].value for j in range(has_value)]
            new_valid_values = [set() for _ in range(len(cages))]
            cages[has_value].update_cage(known_values, cages, new_valid_values, cage_sum)

            next_assign = None
            for i in range(has_value, len(cages)):
                cages[i].valid_values = cages[i].valid_values.intersection(new_valid_values[i])
                if len(new_valid_values[i]) == 1:
                    next_assign = cages[i]
            return next_assign

    def update_cage(self, known_values: list[int], cages: list[_KilVertex], new_valid_values:
                    list[set[int]], cage_sum: int) -> bool:
        """Update the valid values of all entries in the cage. A valid value is added to one of
        the new_valid_values if it appears in a combination whose sum equals the given cage_sum
        and that there is no two entries in this cage have the same value if they are neighbours
        of each other."""
        if len(known_values) == len(cages) - 1:
            valid_value = cage_sum - sum(known_values)
            if valid_value not in self.valid_values:
                return False

            for j in range(len(known_values)):
                if cages[j] in self.neighbours and valid_value == known_values[j]:
                    return False

            new_valid_values[len(known_values)].add(valid_value)
            return True

        next_entry = cages[len(known_values) + 1]
        result = False
        for valid_value in self.valid_values:
            if valid_value + sum(known_values) < cage_sum and all(cages[i] not in self.neighbours
                                                                  or valid_value != known_values[i]
                                                                  for i in
                                                                  range(len(known_values))):
                if next_entry.update_cage(known_values + [valid_value], cages, new_valid_values,
                                          cage_sum):
                    new_valid_values[len(known_values)].add(valid_value)
                    result = True

        return result


@dataclass
class Cage:
    """A cage in a Killer Sudoku game.

    This dataclass is meant to be used by instances of Sudoku.

    Public attributes:
        - sum: an integer that indicates the sum of the numbers of in the cage.
        - coordinates: a set of coordinates of the entry in this cage.
    """
    sum: int
    coordinates: list[tuple[int, int]]


@dataclass
class IndirectCage:
    """An indirect cage in a Killer Sudoku game.

    This class is meant to be used for the attribute of a _KilVertex.

    Public attributes:
        - sum: the sum that this indirect cage must add up to.
        - entries: the set of entry in the Killer Sudoku puzzle that is in this indirect cage.
    """
    sum: int
    entries: list[_KilVertex]


def sudoku_dataset(sudoku_puzzle: Sudoku) -> None:
    """Create a sudoku dataset by repeatedly calling the sudoku.generate_puzzle() function
    and appending outputted puzzle to list and storing it to a file using pickle."""
    with open('killer_sudoku.pkl', 'wb') as file:
        puzzles = []
        for _ in range(10):
            puzzle = sudoku_puzzle.generate_puzzle()
            puzzles.append(puzzle)

        pickle.dump(puzzles, file)


if __name__ == '__main__':
    import python_ta.contracts
    python_ta.contracts.check_all_contracts()

    python_ta.check_all()

    python_ta.check_all(config={
        'extra-imports': ['pickle', 'random', 'copy', 'pprint'],
        'allowed-io': ['solve', 'print_puzzle', 'generate_puzzle', 'generate', 'sudoku_dataset'],
        'max-line-length': 100,
        'disable': ['E1136'],
        'max-nested-blocks': 4,
    })
