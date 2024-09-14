from tkinter import Tk, Canvas, Frame, OptionMenu, IntVar, StringVar, BOTH, Radiobutton, Button, Label, RIGHT, LEFT, W
from tkinter.ttk import Style
import os
import time
from collections import deque, defaultdict

# Constants
GRID_SIZE = 450
CONTROL_PANEL_WIDTH = 250
TOTAL_WIDTH = GRID_SIZE + CONTROL_PANEL_WIDTH
HEIGHT = 500
MARGIN = 20
SIDE = 45

class SudokuGame:
    def __init__(self):
        self.puzzles = {'Easy': [], 'Medium': [], 'Hard': []}
        self.puzzle = [[0] * 9 for _ in range(9)]
        self.original_puzzle = [[0] * 9 for _ in range(9)]  # To store the original puzzle state

    def load_puzzles(self):
        """ Load all puzzles from external text files """
        self.puzzles['Easy'] = self._read_puzzle_file('easy_puzzles.txt')
        self.puzzles['Medium'] = self._read_puzzle_file('medium_puzzles.txt')
        self.puzzles['Hard'] = self._read_puzzle_file('hard_puzzles.txt')

    def _read_puzzle_file(self, filename):
        puzzles = []
        current_puzzle = []
        try:
            with open(filename) as f:
                for line in f:
                    line = line.strip()
                    if line and (line.isnumeric() or line.replace(" ", "").isdigit()):
                        current_puzzle.append(list(map(int, line.split())))
                    elif current_puzzle:
                        puzzles.append(current_puzzle)
                        current_puzzle = []
                if current_puzzle:
                    puzzles.append(current_puzzle)
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        return puzzles

    def load_puzzle(self, difficulty, index):
        """ Load a puzzle into the game based on difficulty and index """
        if difficulty in self.puzzles and index < len(self.puzzles[difficulty]):
            self.puzzle = self.puzzles[difficulty][index]
            self.original_puzzle = [row[:] for row in self.puzzle]

    def check_win(self):
        """ Check if the current grid is a solved Sudoku puzzle """
        for row in self.puzzle:
            if any(cell == 0 for cell in row):
                return False
        return True

    def find_empty_cell(self):
        """ Find an empty cell (with value 0) in the current grid """
        for i in range(9):
            for j in range(9):
                if self.puzzle[i][j] == 0:
                    return i, j
        return None

    def is_valid(self, num, row, col):
        """ Check if a number can be placed at the given cell """
        # Check the row
        if num in self.puzzle[row]:
            return False
        # Check the column
        if num in [self.puzzle[i][col] for i in range(9)]:
            return False
        # Check the 3x3 grid
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(3):
            for j in range(3):
                if self.puzzle[start_row + i][start_col + j] == num:
                    return False
        return True

    def backtracking_solve(self):
        """ Solve the current Sudoku grid using the backtracking algorithm """
        empty_cell = self.find_empty_cell()
        if not empty_cell:
            return True  # Puzzle solved

        row, col = empty_cell
        for num in range(1, 10):
            if self.is_valid(num, row, col):
                self.puzzle[row][col] = num
                if self.backtracking_solve():
                    return True
                self.puzzle[row][col] = 0

        return False

    def timed_backtracking_solve(self):
        """ Measure time taken to solve using backtracking """
        start = time.time()
        solved = self.backtracking_solve()
        end = time.time()
        return solved, end - start

    def ac3_solve(self):
        """Apply the AC-3 algorithm to reduce domains and potentially solve the Sudoku puzzle."""
        def get_neighbors(row, col):
            """Get all neighboring cells that need to be checked for consistency."""
            neighbors = set()
            block_row, block_col = row - row % 3, col - col % 3
            for k in range(9):
                if k != col:
                    neighbors.add((row, k))  # Same row
                if k != row:
                    neighbors.add((k, col))  # Same column
                # Block neighbors
                neighbors.add((block_row + k // 3, block_col + k % 3))
            neighbors.discard((row, col))
            return neighbors

        def get_domain(puzzle, row, col):
            """Return possible values for a cell by eliminating values from row, column, and block."""
            if puzzle[row][col] != 0:
                return {puzzle[row][col]}
            allowed = set(range(1, 10))
            block_row, block_col = row - row % 3, col - col % 3
            for k in range(9):
                allowed.discard(puzzle[row][k])
                allowed.discard(puzzle[k][col])
                allowed.discard(puzzle[block_row + k // 3][block_col + k % 3])
            return allowed

        # Initialize all domains for every cell
        domains = {(row, col): get_domain(self.puzzle, row, col) for row in range(9) for col in range(9)}

        def revise(xi, xj):
            """Revise xi's domain to ensure it's consistent with xj's."""
            revised = False
            xj_domain = domains[xj]
            xi_domain = domains[xi]
            if len(xi_domain) == 1:
                if xi_domain & xj_domain:
                    xj_domain -= xi_domain
                    revised = True
            return revised

        # Initialize a queue only with empty cells
        queue = deque((row, col) for row in range(9) for col in range(9) if self.puzzle[row][col] == 0)

        while queue:
            row, col = queue.popleft()
            for neighbor in get_neighbors(row, col):
                assert neighbor in domains, f"Neighbor {neighbor} not found in domains"
                if revise((row, col), neighbor):
                    if len(domains[(row, col)]) == 0:
                        return False  # Failure
                    queue.append(neighbor)

        # Apply values if domains are reduced to single choices
        for row, col in domains:
            if len(domains[(row, col)]) == 1:
                self.puzzle[row][col] = domains[(row, col)].pop()

        if not self.check_win():
            self.backtracking_solve()

        return True

    def timed_ac3_solve(self):
        """ Measure time taken to solve using AC-3 """
        start = time.time()
        solved = self.ac3_solve()
        end = time.time()
        return solved, end - start
    
    def start(self):
        """Reset the puzzle to its original state."""
        self.puzzle = [row[:] for row in self.original_puzzle]  # Restore from the original copy

class SudokuUI(Frame):
    def __init__(self, parent, game):
        self.game = game
        self.parent = parent
        Frame.__init__(self, parent)
        self.row, self.col = 0, 0
        self.algorithm_var = StringVar(value="Arc Consistency-3")
        self.puzzle_var = IntVar(value=1)
        self.game_level_var = StringVar()
        self.game_level_var.set("Easy")
        self.time_label = None  # Store reference to the time label
        self.__initUI()
        self.game.load_puzzles()

    def __initUI(self):
        self.parent.title("Sudoku")
        self.pack(fill=BOTH, expand=1)

        # Create a style for better UI
        style = Style()
        style.configure("TButton", font=("Helvetica", 10), padding=5)

        # Frame for the grid on the left side
        left_frame = Frame(self, borderwidth=2, relief="sunken", bg="lightgray")
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)

        # Canvas for Sudoku grid
        self.canvas = Canvas(left_frame, width=GRID_SIZE, height=GRID_SIZE, bg="pink")
        self.canvas.pack(fill=BOTH, expand=True)
        self.__draw_grid()
        self.__draw_puzzle()

        # Frame for controls on the right side
        right_frame = Frame(self, borderwidth=2, relief="ridge", bg="white")
        right_frame.pack(side=RIGHT, fill='y', padx=10, pady=10)

        # Dropdown for game level
        Label(right_frame, text="Level:", bg="pink").pack(pady=5)
        game_levels = ["Easy", "Medium", "Hard"]
        self.game_level_menu = OptionMenu(right_frame, self.game_level_var, *game_levels, command=self.__update_puzzle)
        self.game_level_menu.pack(pady=5)

        # Algorithm selection radio buttons
        Label(right_frame, text="Algorithms:", bg="pink").pack(pady=5)
        Radiobutton(right_frame, text="Arc Consistency-3", variable=self.algorithm_var, value="Arc Consistency-3", bg="white").pack(anchor=W)
        Radiobutton(right_frame, text="Backtracking", variable=self.algorithm_var, value="Backtracking", bg="white").pack(anchor=W)

        # Puzzle selection radio buttons
        Label(right_frame, text="Choose Puzzle:", bg="pink").pack(pady=5)
        for i in range(1, 5):
            Radiobutton(right_frame, text=f"Puzzle {i}", variable=self.puzzle_var, value=i, bg="white", command=self.__update_puzzle).pack(anchor=W)

        # Buttons for control (with increased width)
        Button(right_frame, text="Reset", command=self.__clear_answers, width=15).pack(pady=5)
        Button(right_frame, text="Solve", command=self.__solve, width=15).pack(pady=5)

        # Time label to show the time taken
        self.time_label = Label(right_frame, text="Time:", bg="pink")
        self.time_label.pack(pady=5)

        # Bindings
        self.canvas.bind("<Button-1>", self.__cell_clicked)
        self.canvas.bind("<Key>", self.__key_pressed)

    def __solve(self):
        """ Solve the puzzle using the selected algorithm and measure the time taken. """
        algorithm = self.algorithm_var.get()
        time_taken = 0
        if algorithm == "Backtracking":
            solved, time_taken = self.game.timed_backtracking_solve()
        elif algorithm == "Arc Consistency-3":
            solved, time_taken = self.game.timed_ac3_solve()

        # Update the time label with the measured time in seconds
        self.time_label.config(text=f"Time: {time_taken:.3f} seconds")

        # Redraw the puzzle after solving
        self.__draw_puzzle()

    def __draw_grid(self):
        for i in range(10):
            color = "blue" if i % 3 == 0 else "gray"
            x0 = MARGIN + i * SIDE
            y0 = MARGIN
            x1 = MARGIN + i * SIDE
            y1 = GRID_SIZE - MARGIN
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

            x0 = MARGIN
            y0 = MARGIN + i * SIDE
            x1 = GRID_SIZE - MARGIN
            y1 = MARGIN + i * SIDE
            self.canvas.create_line(x0, y0, x1, y1, fill=color)

    def __draw_puzzle(self):
        self.canvas.delete("numbers")
        for i in range(9):
            for j in range(9):
                answer = self.game.puzzle[i][j]
                original = self.game.original_puzzle[i][j]
                if answer != 0:
                    x = MARGIN + j * SIDE + SIDE / 2
                    y = MARGIN + i * SIDE + SIDE / 2
                    color = "black" if answer == original else "blue"
                    self.canvas.create_text(x, y, text=answer, tags="numbers", fill=color)

    def __update_puzzle(self, _=None):
        """ Update the grid with the selected puzzle """
        difficulty = self.game_level_var.get()
        puzzle_index = self.puzzle_var.get() - 1
        self.game.load_puzzle(difficulty, puzzle_index)
        self.__draw_puzzle()

    def __clear_answers(self):
        self.game.start()
        self.canvas.delete("victory")
        self.__draw_puzzle()

    def __cell_clicked(self, event):
        if self.game.check_win():
            return
        x, y = event.x, event.y
        if (MARGIN < x < GRID_SIZE - MARGIN and MARGIN < y < GRID_SIZE - MARGIN):
            self.canvas.focus_set()
            row, col = (y - MARGIN) // SIDE, (x - MARGIN) // SIDE
            if (row, col) == (self.row, self.col):
                self.row, self.col = -1, -1
            elif self.game.puzzle[row][col] == 0:
                self.row, col = row, col
        self.__draw_cursor()

    def __key_pressed(self, event):
        if self.game.check_win():
            return
        if self.row >= 0 and self.col >= 0 and event.char in "1234567890":
            self.game.puzzle[self.row][self.col] = int(event.char)
            self.col, self.row = -1, -1
            self.__draw_puzzle()
            self.__draw_cursor()

    def __draw_cursor(self):
        self.canvas.delete("cursor")
        if self.row >= 0 and self.col >= 0:
            x0 = MARGIN + self.col * SIDE + 1
            y0 = MARGIN + self.row * SIDE + 1
            x1 = MARGIN + (self.col + 1) * SIDE - 1
            y1 = MARGIN + (self.row + 1) * SIDE - 1
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", tags="cursor")

def main():
    root = Tk()
    game = SudokuGame()
    SudokuUI(root, game)
    root.geometry(f"{TOTAL_WIDTH}x{HEIGHT}")
    root.mainloop()

if __name__ == "__main__":
    main()


 