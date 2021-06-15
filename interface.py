"""CSC111 Winter 2021 Project: Sudoku Solver

This module contains the user interface implementation of the Sudoku solvers.

Copyright and Usage Information
===============================

This file is Copyright (c) 2021 Raymond Liu
"""
import pyglet
from pyglet.shapes import Line, Rectangle
from pyglet.text import Label
from pyglet.window import key
from pyglet import clock
from sudoku import ClassicSudoku, _ClaVertex, Optional, KillerSudoku, _KilVertex, Cage, \
    IndirectCage, Union


class SudokuWindow(pyglet.window.Window):
    """A user interactive window for Sudoku solvers.

    Attributes:
        - sudoku_dict: a dictionary that maps 'Classic' to an instance of ClassicSudoku, and
        maps 'Killer' to an instance of KillerSudoku.
        - mode: the mode of the current puzzle. It can either be 'Classic' or 'Killer'.
        - sudoku: an instance of Sudoku that is currently being displayed and solved.
        - batch: an instance of pyglet.graphics.Batch() that can draw multiple pyglet.shapes
        objects and pyglet.text at once to improve drawing speed.
        - outlines: a list of Line objects for the outline of the Sudoku puzzle.
        - numbers: a dictionary that maps the coordinate of an entry (e.g. (1, 1), (9, 9) )
        to the Label object of that entry.
        - cage_lines: a list of Line and Label objects for the cage lines of a Killer Sudoku.
        - buttons: a list of Line and Label objects for the buttons in the window.
        - button_info: a list of 4-tuples, each containing the screen coordinate as well as
        the width and height of a button.
        - cell_side: the length of a cell on screen.
        - track_mouse: a Rectangle object that appears when the users hover their mouse onto
        a cell or a button, and disappear (get deleted) otherwise.
        - invalid_msg: a Label object that displays the message "Invalid Input!" to the user
        when they made an invalid input to a cell.
        - error_msg: a Label object that displays the message "Puzzle Unsolvable" to the user
        when the current Sudoku puzzle is unsolvable.
        - fade: an integer that influences the color of the two messages so that they fade
        after 1 second or so.
        - mx: the x coordinate of the mouse.
        - my: the y coordinate of the mouse.
    """
    sudoku_dict: dict[str, Union[ClassicSudoku, KillerSudoku]]
    mode: str
    sudoku: Union[ClassicSudoku, KillerSudoku]
    batch: pyglet.graphics.Batch
    outlines: list[Line]
    numbers: dict[tuple[int, int], Label]
    cage_lines: list[Union[Line, Label]]
    buttons: list[Union[Line, Label]]
    button_info: list[tuple[int, int, int, int]]
    cell_side: int
    track_mouse: Optional[Rectangle]
    invalid_msg: Label
    error_msg: Label
    fade: int
    mx: Optional[int]
    my: Optional[int]

    def __init__(self) -> None:
        """Initialize the Pyglet window."""
        super(SudokuWindow, self).__init__(width=950, height=700, resizable=True,
                                           caption='Sudoku solver')
        self.sudoku_dict = {'Classic': ClassicSudoku(), 'Killer': KillerSudoku()}
        self.mode = 'Classic'
        self.sudoku = self.sudoku_dict[self.mode]

        self.batch = pyglet.graphics.Batch()
        self.outlines = []
        self.numbers = {}
        self.cage_lines = []
        self.buttons = []
        self.button_info = [(710, 160, 200, 45), (710, 220, 200, 45), (710, 280, 200, 45),
                            (760, 490, 100, 31), (760, 530, 100, 31)]
        self.cell_side = 60
        self.track_mouse = None
        self.invalid_msg = Label("Invalid Input!", font_name='Times New Roman', font_size=23,
                                 color=(255, 0, 0, 0), x=825, y=80, anchor_x='center',
                                 anchor_y='bottom', batch=self.batch)
        self.error_msg = Label("Puzzle Unsolvable!", font_name='Times New Roman', font_size=23,
                               color=(255, 0, 0, 0), x=825, y=80, anchor_x='center',
                               anchor_y='bottom', batch=self.batch)
        self.fade = 0
        self.mx = None
        self.my = None

        self.draw_sudoku_outline()
        self.draw_entry_values()
        self.draw_buttons()

    def on_draw(self) -> None:
        """Perform the initial drawing when the window prompts."""
        pyglet.gl.glClearColor(1, 1, 1, 1)
        self.clear()
        self.batch.draw()

    def draw_sudoku_outline(self) -> None:
        """Draw the outline of the Sudoku puzzle."""
        for i in range(10):
            if i % 3 == 0:
                width = 4
            else:
                width = 2
            self.outlines.append(Line(80 + self.cell_side * i, 80, 80 + self.cell_side * i, 620,
                                      width, (0, 0, 0), batch=self.batch))
            self.outlines.append(Line(80, 80 + self.cell_side * i, 620, 80 + self.cell_side * i,
                                      width, (0, 0, 0), batch=self.batch))

    def draw_entry_values(self) -> None:
        """Delete all previous label for entry values and recreate labels for all entries
        that has a value."""
        for coord in self.numbers:
            self.numbers[coord].delete()

        self.numbers = {}

        for y in range(1, 10):
            for x in range(1, 10):
                value = self.sudoku.get_entry(x, y)
                if value is not None:
                    self.numbers[(x, y)] = self.entry_label(x, y, value)

    def entry_label(self, x: int, y: int, value: int) -> Label:
        """Return a Label instance representing the entry at (x, y) with <value>."""
        return Label(str(value), font_size=30, color=(0, 0, 0, 255), x=50 + self.cell_side * x,
                     y=650 - self.cell_side * y, anchor_x='center', anchor_y='center',
                     batch=self.batch)

    def clear_cage(self) -> None:
        """Delete all cage lines."""
        for cage_line in self.cage_lines:
            cage_line.delete()

        self.cage_lines = []

    def draw_cage(self) -> None:
        """Display the cages and the cage sum when the mode is Killer.

        The location of the cage sum will always be the top-left corner of the cage.
        """
        for cage in self.sudoku.cages:
            min_x, min_y = None, None
            lines = []
            for x, y in cage.coordinates:
                for ax, ay in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                    if (ax, ay) not in cage.coordinates:
                        lines.append(self.cage_line(x, y, ax, ay, cage.coordinates))

                if min_x is None or min_y is None or x + y < min_x + min_y or \
                        x + y == min_x + min_y and y < min_y:
                    min_x, min_y = x, y

            self.cage_lines.append(self.create_cage_sum(min_x, min_y, cage.sum, lines))
            self.cage_lines.extend(lines)

    def cage_line(self, x: int, y: int, ax: int, ay: int, cages: list[tuple[int, int]]) -> Line:
        """Return a cage line based on the adjacent entries.

        Draw a cage line on a side of an entry when its adjacent entry on that side is not
        in the same cage, and that line is drawn with extra length when the adjacent entries
        on the direction of line is in the same cage.
        """
        cx, cy = (20 + x * self.cell_side, 620 - y * self.cell_side)
        if (ax, ay) == (x + 1, y):
            lx1, ly1, lx2, ly2 = self.extend_line1(x, y, cx, cy, cages, True)
        elif (ax, ay) == (x - 1, y):
            lx1, ly1, lx2, ly2 = self.extend_line1(x, y, cx, cy, cages, False)
        elif (ax, ay) == (x, y + 1):
            lx1, ly1, lx2, ly2 = self.extend_line2(x, y, cx, cy, cages, False)
        else:
            lx1, ly1, lx2, ly2 = self.extend_line2(x, y, cx, cy, cages, True)
        return Line(lx1, ly1, lx2, ly2, width=1, color=(0, 0, 230), batch=self.batch)

    def extend_line1(self, x: int, y: int, cx: int, cy: int, cages: list[tuple[int, int]],
                     right: bool) -> tuple[int, int, int, int]:
        """Extend the line depending on whether its adjacent entry is in the cage or not."""
        if right:
            extension = self.cell_side - 5
        else:
            extension = 5
        if (x, y + 1) in cages:
            lx1, ly1 = cx + extension, cy - 5
        else:
            lx1, ly1 = cx + extension, cy + 5
        if (x, y - 1) in cages:
            lx2, ly2 = cx + extension, cy + self.cell_side + 5
        else:
            lx2, ly2 = cx + extension, cy + self.cell_side - 5
        return lx1, ly1, lx2, ly2

    def extend_line2(self, x: int, y: int, cx: int, cy: int, cages: list[tuple[int, int]],
                     right: bool) -> tuple[int, int, int, int]:
        """Extend the line depending on whether its adjacent entry is in the cage or not."""
        if right:
            extension = self.cell_side - 5
        else:
            extension = 5
        if (x - 1, y) in cages:
            lx1, ly1 = cx - 5, cy + extension
        else:
            lx1, ly1 = cx + 5, cy + extension
        if (x + 1, y) in cages:
            lx2, ly2 = cx + self.cell_side + 5, cy + extension
        else:
            lx2, ly2 = cx + self.cell_side - 5, cy + extension
        return lx1, ly1, lx2, ly2

    def create_cage_sum(self, x: int, y: int, cage_sum: int, lines: list[Line]) -> Label:
        """Reduce the length of the two line segments to create space for the cage sum label,
        and return that label."""
        sx, sy = (20 + x * self.cell_side, 680 - y * self.cell_side)
        for line in lines:
            if line.x - 5 == sx and line.y == sy - 5:
                line.x += 6 * len(str(cage_sum))
            elif line.x2 - 5 == sx and line.y2 == sy - 5:
                line.y2 -= 10
        return Label(str(cage_sum), font_size=10, bold=True, color=(0, 0, 0, 255), x=sx + 3,
                     y=sy - 3, anchor_x='left', anchor_y='top', batch=self.batch)

    def tracking_highlight(self, x: int, y: int, width: int, height: int) -> None:
        """Create a rectangle at (x, y) with the given width and height, assign it to
        self.track_mouse, and make it somewhat transparent."""
        self.track_mouse = Rectangle(x, y, width, height, color=(153, 204, 255), batch=self.batch)
        self.track_mouse.opacity = 50

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        """Check if the mouse is on a cell or a button. If yes, highlight that cell or
        button. Otherwise, remove the highlight."""
        self.mx, self.my = x, y
        on_button = self.on_button(x, y)
        on_cell = self.on_cell(x, y)
        if on_cell is not None:
            self.tracking_highlight(on_cell[2], on_cell[3], 60, 60)
        elif on_button is not None:
            x, y, width, height, _ = on_button
            self.tracking_highlight(x, y, width, height)
        else:
            if self.track_mouse is not None:
                self.track_mouse.delete()
                self.track_mouse = None

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """If the current mode is 'Classic', check if the mouse is on a cell or not. If yes,
        add, change or delete the value of that cell accordingly."""
        if self.mode == 'Killer':
            return

        input_string = chr(symbol)
        cell = self.on_cell(self.mx, self.my)
        if cell is not None:
            cx, cy = cell[0], cell[1]
            if input_string.isnumeric() and int(input_string) != 0:
                num = int(input_string)

                if self.sudoku.change_entry(cx, cy, num):
                    if (cx, cy) in self.numbers:
                        self.numbers[(cx, cy)].delete()

                    self.numbers[(cx, cy)] = self.entry_label(cx, cy, num)
                else:
                    if self.fade != 0:
                        self.fade = 0
                        clock.unschedule(self.puzzle_unsolvable)
                        self.error_msg.color = (255, 0, 0, 0)
                    clock.schedule_interval(self.invalid_input, 0.055)

            elif symbol == key.BACKSPACE:
                self.sudoku.clear_entry(cx, cy)
                if (cx, cy) in self.numbers:
                    self.numbers[(cx, cy)].delete()
                    self.numbers.pop((cx, cy), None)

    def on_mouse_release(self, x: int, y: int, button: bool, modifiers: int) -> None:
        """Check if the mouse is on a button. If yes, execute the corresponding function of
        that button."""
        button = self.on_button(x, y)
        if button is not None:
            _, _, _, _, name = button
            if name == 'Clear':
                self.sudoku.clear()
                self.clear_cage()
            elif name == 'Generate':
                if self.mode == 'Classic':
                    self.sudoku.generate('classic_sudoku.pkl')
                else:
                    self.clear_cage()
                    self.sudoku.generate('human_killer_sudoku.pkl')
                    self.draw_cage()
            elif name == 'Solve':
                if not self.sudoku.solve():
                    if self.fade != 0:
                        self.fade = 0
                        clock.unschedule(self.invalid_input)
                        self.invalid_msg.color = (255, 0, 0, 0)
                    clock.schedule_interval(self.puzzle_unsolvable, 0.055)
            elif name == 'Killer':
                self.mode = 'Killer'
                self.sudoku = self.sudoku_dict[self.mode]
                self.draw_cage()
            elif name == 'Classic':
                self.mode = 'Classic'
                self.sudoku = self.sudoku_dict[self.mode]
                self.clear_cage()
            self.draw_entry_values()

    def draw_buttons(self) -> None:
        """Create Line and Label objects for the buttons."""
        self.buttons.append(Line(670, 0, 670, 700, width=2, color=(0, 0, 0), batch=self.batch))
        self.buttons.append(Label('Mode', font_name='Times New Roman', font_size=35,
                                  color=(0, 0, 0, 255), x=810, y=580, anchor_x='center',
                                  anchor_y='baseline', batch=self.batch))

        names = ['Clear', 'Generate', 'Solve', 'Killer', 'Classic']
        for i in range(len(self.button_info)):
            x, y, width, height = self.button_info[i]
            objects = [
                Label(names[i], x=x + width // 2, y=y + height // 2, font_name='Times New Roman',
                      font_size=19.5 + 5 * int(i < 3), color=(0, 0, 0, 255), anchor_x='center',
                      anchor_y='center', batch=self.batch),
                Line(x, y, x + width, y, width=2.5, color=(0, 0, 0), batch=self.batch),
                Line(x, y + height, x + width, y + height, width=2.5, color=(0, 0, 0),
                     batch=self.batch),
                Line(x, y, x, y + height, width=2.5, color=(0, 0, 0), batch=self.batch),
                Line(x + width, y, x + width, y + height, width=2.5, color=(0, 0, 0),
                     batch=self.batch)]

            self.buttons.extend(objects)

        self.buttons.append(Line(670, 380, 950, 380, width=2, color=(0, 0, 0), batch=self.batch))

    def on_button(self, mx: int, my: int) -> Optional[tuple[int, int, int, int, str]]:
        """If the given coordinate (mx, my) is above a button, return the button's left-bottom
        corner coordinate, its width, its height, and its name as a 5-tuple. Otherwise, return None.
        """
        names = ['Clear', 'Generate', 'Solve', 'Killer', 'Classic']
        for i in range(len(self.button_info)):
            x, y, width, height = self.button_info[i]
            if x <= mx <= x + width and y <= my <= y + height:
                return (x, y, width, height, names[i])

        return None

    def on_cell(self, mx: int, my: int) -> Optional[tuple[int, int, int, int]]:
        """If the given coordinate (mx, my) is above a cell, return the cell's coordinate (x, y)
        where 1 <= x, y <= 9, as well as its left corner coordinate on the screen. Otherwise,
        return None."""
        coordinate = ((mx - 80) // self.cell_side + 1, 9 - (my - 80) // self.cell_side)
        if 1 <= coordinate[0] <= 9 and 1 <= coordinate[1] <= 9:
            return (coordinate[0], coordinate[1],
                    80 + (coordinate[0] - 1) * self.cell_side,
                    80 + (9 - coordinate[1]) * self.cell_side)

        return None

    def invalid_input(self, dt: float) -> None:
        """Display the message "Invalid Input!" at the right bottom corner.

        The color of this message fades every time this method is called, and eventually
        disappear after 51 times.
        """
        self.invalid_msg.color = (255, 0, 0, 255 - 5 * self.fade)
        if self.fade == 51:
            self.fade = 0
            clock.unschedule(self.invalid_input)
        else:
            self.fade += 1

    def puzzle_unsolvable(self, dt: float) -> None:
        """Display the message "Puzzle Unsolvable!" at the right bottom corner.

        The color of this message fades every time this method is called, and eventually
        disappear after 51 times.
        """
        self.error_msg.color = (255, 0, 0, 255 - 5 * self.fade)
        if self.fade == 51:
            self.fade = 0
            clock.unschedule(self.puzzle_unsolvable)
        else:
            self.fade += 1


if __name__ == '__main__':
    import python_ta.contracts
    python_ta.contracts.check_all_contracts()

    python_ta.check_all()

    python_ta.check_all(config={
        'extra-imports': ['pyglet', 'sudoku', 'pyglet.shapes', 'pyglet.text', 'pyglet.window'],
        'allowed-io': [],
        'max-line-length': 100,
        'disable': ['E1136'],
        'max-nested-blocks': 4,
    })
    # In pyglet tutorial, children of pyglet.window.Window does not need to
    # implement all abstract methods.
    #
    # The dt parameter for invalid_input and puzzle_unsolvable is required for
    # clock.schedule_interval
