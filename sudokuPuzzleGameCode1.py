import random
import time
import json
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, font
from typing import List, Tuple, Optional
import threading

# Define color scheme - UNCHANGED
COLORS = {
    "bg_dark": "#131313",  #dark gray for background
    "bg_medium": "#094E86",  #blue for grid
    "bg_light": "#5798C0",  #lighter blue also for the grid
    "accent": "#FF0000",  #rred accent color
    "accent_hover": "#C0392B",  #red for hover states
    "text_light": "#ECF0F1",  
    "text_dark": "#2C3E50",  
    "highlight": "#3498DB",  
    "error": "#FF5252",  # Error color
    "success": "#2ECC71",  # Success color
    "original_cell": "#000000",  #black for the original cells, it represents the numbers that are already in the puzzle
    "user_cell": "#FFFFFF",  #white for user-entered cells (ours when we type in a value this is the color itll be displayed in)
    "selected": "#0276BB",  #selected cell color
    "invalid": "#E74C3C",  #invalid cell color
}

class SudokuSolver:
  
    #integrated sudoku solver application with GUI interface which ccombines genetic and backtracking algorithms with an interactive interface/GUI.
   
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.configure(bg=COLORS["bg_dark"])
        
        self.setup_styles()
        
       
        self.size = 9
        self.box_size_rows = 3  #number of rows in each box
        self.box_size_cols = 3  #number of columns in each box
        self.algorithm = "genetic"  #default algorithm to be selected when we first run the code
        self.solving = False
        self.solver_thread = None
        
        #game state
        self.current_board = []
        self.original_board = []
        self.flattened_board = ""
        self.selected_cell = (-1, -1)
        
        #tracking any invalid cells for highlighting
        self.invalid_cells = set()
        
        #solving statistics
        self.iterations = 0
        self.elapsed_time = 0.0
        self.memory_used = 0.0
        self.fitness = 0
        self.start_time = 0  #this tracks when the solving starts
        
    
        self.create_ui() #create UI componenets
        self.new_game() #genearting a new game when we first run the code

        self.update_stats_display()
    
    def setup_styles(self):
       #the following sets up custom styles for ttk widgets
        style = ttk.Style()
        
        #this si for configuring the progress bar style
        style.configure("TProgressbar", 
                       thickness=8,
                       troughcolor=COLORS["bg_medium"],
                       background=COLORS["accent"])
   
        style.configure("TCombobox",
                       fieldbackground=COLORS["text_light"],  
                       background=COLORS["bg_medium"],
                       foreground=COLORS["text_dark"],       
                       arrowcolor=COLORS["accent"])          
        

        self.root.option_add('*TCombobox*Listbox.background', COLORS["text_light"])
        self.root.option_add('*TCombobox*Listbox.foreground', COLORS["text_dark"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLORS["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', COLORS["text_light"])
        
        #configuring the radio button style
        style.configure("TRadiobutton",
                       background=COLORS["bg_medium"],
                       foreground=COLORS["text_light"])
    
    def create_ui(self):
        """Create all UI components"""
        #here we are splitting into left and right panels
        main_frame = tk.Frame(self.root, bg=COLORS["bg_dark"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        #so the left panel shows game board and controls
        left_panel = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        #and the right panel shows the algorithm selection and stats
        right_panel = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        #this is the top frame that shows title and size selection
        top_frame = tk.Frame(left_panel, bg=COLORS["bg_dark"])
        top_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(top_frame, text="SUDOKU SOLVER", 
                              font=("Arial", 24, "bold"), 
                              bg=COLORS["bg_dark"], 
                              fg=COLORS["accent"])
        title_label.pack(side=tk.LEFT)
        
        #for board size selection
        size_frame = tk.Frame(top_frame, bg=COLORS["bg_dark"])
        size_frame.pack(side=tk.RIGHT)
        
  
        size_label = tk.Label(size_frame, text="Board Size:", 
                             bg=COLORS["bg_dark"], 
                             fg=COLORS["accent"], 
                             font=("Arial", 12, "bold")) 
        size_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.size_var = tk.StringVar(value="9×9")
        size_options = ["3×3", "6×6", "9×9"]
        size_dropdown = ttk.Combobox(size_frame, textvariable=self.size_var, 
                                    values=size_options, width=5, style="TCombobox")
        size_dropdown.pack(side=tk.LEFT)
        size_dropdown.bind("<<ComboboxSelected>>", self.change_board_size)
        
    
        board_container = tk.Frame(left_panel, bg=COLORS["bg_medium"], 
                                  bd=0, relief=tk.RAISED, padx=10, pady=10)
        board_container.pack(pady=10)
        
        self.game_frame = tk.Frame(board_container, bg=COLORS["bg_medium"], bd=2)
        self.game_frame.pack(padx=5, pady=5)
        
        #this is the number buttons frame 
        num_buttons_frame = tk.Frame(left_panel, bg=COLORS["bg_dark"])
        num_buttons_frame.pack(pady=15)
        
        #creating the number buttons
        self.num_buttons = []
        for i in range(1, 10):
            btn = tk.Button(num_buttons_frame, text=str(i), width=3, height=1,
                           font=("Arial", 14, "bold"),
                           bg=COLORS["bg_medium"],
                           fg=COLORS["text_light"],
                           activebackground=COLORS["accent"],
                           activeforeground=COLORS["text_light"],
                           relief=tk.RAISED,
                           bd=0,
                           command=lambda num=i: self.set_number(num))
            btn.grid(row=(i-1)//5, column=(i-1)%5, padx=5, pady=5)
            self.num_buttons.append(btn)
        
        #adding the clear button
        clear_btn = tk.Button(num_buttons_frame, text="Clear", width=7, height=1,
                             font=("Arial", 12),
                             bg=COLORS["bg_light"],
                             fg=COLORS["text_light"],
                             activebackground=COLORS["accent"],
                             activeforeground=COLORS["text_light"],
                             relief=tk.RAISED,
                             bd=0,
                             command=lambda: self.set_number(0))
        clear_btn.grid(row=1, column=4, padx=5, pady=5)
        
        #for the control buttons frame
        control_frame = tk.Frame(left_panel, bg=COLORS["bg_dark"])
        control_frame.pack(pady=10, fill=tk.X)
        
        #for the solve button
        self.solve_btn = tk.Button(control_frame, text="SOLVE", width=10, height=2,
                                  font=("Arial", 12, "bold"),
                                  bg=COLORS["accent"],
                                  fg=COLORS["text_light"],
                                  activebackground=COLORS["accent_hover"],
                                  activeforeground=COLORS["text_light"],
                                  relief=tk.RAISED,
                                  bd=0,
                                  command=self.solve_puzzle)
        self.solve_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        #creating the new game button
        new_game_btn = tk.Button(control_frame, text="NEW GAME", width=10, height=2,
                                font=("Arial", 12),
                                bg=COLORS["bg_medium"],
                                fg=COLORS["text_light"],
                                activebackground=COLORS["accent"],
                                activeforeground=COLORS["text_light"],
                                relief=tk.RAISED,
                                bd=0,
                                command=self.new_game)
        new_game_btn.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.X, expand=True)
        
        #and this si the check button which checks the solution made by the player (us)
        check_btn = tk.Button(control_frame, text="CHECK", width=10, height=2,
                             font=("Arial", 12),
                             bg=COLORS["bg_medium"],
                             fg=COLORS["text_light"],
                             activebackground=COLORS["accent"],
                             activeforeground=COLORS["text_light"],
                             relief=tk.RAISED,
                             bd=0,
                             command=self.check_solution)
        check_btn.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        #algorithm selection frame to allow the user to select the algorithm they want to use
        algo_frame = tk.LabelFrame(right_panel, text="Algorithm", 
                                  bg=COLORS["bg_medium"], 
                                  fg=COLORS["text_light"],
                                  font=("Arial", 12, "bold"),
                                  padx=10, pady=10)
        algo_frame.pack(fill=tk.X, pady=(0, 15))
        
        #make the algortim radio buttons
        self.algo_var = tk.StringVar(value="genetic")
        genetic_radio = tk.Radiobutton(algo_frame, text="Genetic Algorithm", 
                                      variable=self.algo_var,
                                      value="genetic", 
                                      bg=COLORS["bg_medium"], 
                                      fg=COLORS["text_light"],
                                      selectcolor=COLORS["bg_dark"],
                                      activebackground=COLORS["bg_medium"],
                                      activeforeground=COLORS["accent"],
                                      font=("Arial", 10))
        genetic_radio.pack(anchor=tk.W, pady=(5, 0))
        
        genetic_desc = tk.Label(algo_frame, 
                               text="Evolves a population of solutions\nover generations", 
                               bg=COLORS["bg_medium"], 
                               fg=COLORS["text_light"],
                               font=("Arial", 8), 
                               justify=tk.LEFT)
        genetic_desc.pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        backtrack_radio = tk.Radiobutton(algo_frame, text="Backtracking", 
                                        variable=self.algo_var,
                                        value="backtracking", 
                                        bg=COLORS["bg_medium"], 
                                        fg=COLORS["text_light"],
                                        selectcolor=COLORS["bg_dark"],
                                        activebackground=COLORS["bg_medium"],
                                        activeforeground=COLORS["accent"],
                                        font=("Arial", 10))
        backtrack_radio.pack(anchor=tk.W, pady=(5, 0))
        
        backtrack_desc = tk.Label(algo_frame, 
                                 text="Systematically tries values and\nbacktracks when needed", 
                                 bg=COLORS["bg_medium"], 
                                 fg=COLORS["text_light"],
                                 font=("Arial", 8), 
                                 justify=tk.LEFT)
        backtrack_desc.pack(anchor=tk.W, padx=20, pady=(0, 5))

        
        #statistics frame
        stats_frame = tk.LabelFrame(right_panel, text="Statistics", 
                                   bg=COLORS["bg_medium"], 
                                   fg=COLORS["text_light"],
                                   font=("Arial", 12, "bold"),
                                   padx=10, pady=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        #progress bar
        progress_frame = tk.Frame(stats_frame, bg=COLORS["bg_medium"])
        progress_frame.pack(fill=tk.X, pady=10)
        
        progress_label = tk.Label(progress_frame, text="Progress:", 
                                 bg=COLORS["bg_medium"], 
                                 fg=COLORS["text_light"])
        progress_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var, 
                                           length=150,
                                           style="TProgressbar")
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
 
        stats_grid = tk.Frame(stats_frame, bg=COLORS["bg_medium"])
        stats_grid.pack(fill=tk.BOTH, pady=10)
        
        #iterations
        tk.Label(stats_grid, text="Iterations:", 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"]).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.iterations_var = tk.StringVar(value="0")
        tk.Label(stats_grid, textvariable=self.iterations_var, 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"],
                font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.E)
        
        #time elapsed
        tk.Label(stats_grid, text="Time elapsed:", 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"]).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.time_var = tk.StringVar(value="0.00s")
        tk.Label(stats_grid, textvariable=self.time_var, 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"],
                font=("Arial", 10, "bold")).grid(row=1, column=1, sticky=tk.E)
        
        #memory used
        tk.Label(stats_grid, text="Memory used:", 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"]).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.memory_var = tk.StringVar(value="0.00 MB")
        tk.Label(stats_grid, textvariable=self.memory_var, 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"],
                font=("Arial", 10, "bold")).grid(row=2, column=1, sticky=tk.E)
        
        #fitness (only for genetic algorithm)
        tk.Label(stats_grid, text="Fitness:", 
                bg=COLORS["bg_medium"], 
                fg=COLORS["text_light"]).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.fitness_var = tk.StringVar(value="N/A")
        self.fitness_label = tk.Label(stats_grid, textvariable=self.fitness_var, 
                                     bg=COLORS["bg_medium"], 
                                     fg=COLORS["text_light"],
                                     font=("Arial", 10, "bold"))
        self.fitness_label.grid(row=3, column=1, sticky=tk.E)
        
        #game status
        status_frame = tk.Frame(left_panel, bg=COLORS["bg_dark"], pady=5)
        status_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready to play")
        status_label = tk.Label(status_frame, textvariable=self.status_var, 
                               bg=COLORS["bg_dark"], 
                               fg=COLORS["text_light"],
                               font=("Arial", 10, "italic"))
        status_label.pack()
 
    def create_board_ui(self):
        #create the Sudoku board UI based on current size
        # Clear existing cells
        for widget in self.game_frame.winfo_children():
            widget.destroy()
        
        #calculate cell size based on board size
        cell_size = 50 if self.size <= 6 else 40
        
        #create cells
        self.cells = []
        self.cell_entries = []
        
        for i in range(self.size):
            row_cells = []
            row_entries = []
            for j in range(self.size):
                
                box_row, box_col = i // self.box_size_rows, j // self.box_size_cols 
                is_even_box = (box_row + box_col) % 2 == 0
                bg_color = COLORS["bg_light"] if is_even_box else COLORS["bg_medium"]
                
                cell_frame = tk.Frame(self.game_frame, 
                                     width=cell_size, 
                                     height=cell_size, 
                                     bg=bg_color, 
                                     highlightbackground=COLORS["bg_dark"],
                                     highlightthickness=1)
                
               
                cell_frame.grid(row=i, column=j)
                cell_frame.grid_propagate(False)  # Keep cell size fixed
                
               
                if i % self.box_size_rows == 0 and i > 0:
                    cell_frame.grid(row=i, column=j, pady=(3, 0))
                if j % self.box_size_cols == 0 and j > 0:
                    cell_frame.grid(row=i, column=j, padx=(3, 0))
                
               
                cell_entry = tk.Entry(cell_frame, 
                                     width=2,
                                     font=("Arial", 16 if self.size <= 6 else 14, "bold"),
                                     bg=bg_color,
                                     fg=COLORS["text_light"],
                                     bd=0,
                                     justify=tk.CENTER, 
                                     insertbackground=COLORS["user_cell"],  
                                     disabledbackground=bg_color,
                                     disabledforeground=COLORS["original_cell"])
                cell_entry.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                
            
                cell_frame.bind("<Button-1>", lambda event, r=i, c=j: self.select_cell(r, c))
                cell_entry.bind("<FocusIn>", lambda event, r=i, c=j: self.select_cell(r, c))
                cell_entry.bind("<KeyPress>", lambda event, r=i, c=j: self.handle_key_press(event, r, c))
                
                row_cells.append(cell_entry)  
                row_entries.append(cell_entry)
            self.cells.append(row_cells)
            self.cell_entries.append(row_entries)
        
        #updating the number buttons based on board size (like 3x3, 6x6, or 9x9)
        for i, btn in enumerate(self.num_buttons):
            if i < self.size:
                btn.grid()
            else:
                btn.grid_remove()
    
    def handle_key_press(self, event, row, col):
        """Handle key press in a cell"""
        if event.char.isdigit() and 0 <= int(event.char) <= self.size:
            #if it is a valid digit input  then we set the number
            self.set_number(int(event.char))
            return "break"  # Prevent default behavior
        elif event.keysym == "BackSpace":
            #backspace to be able to clear the cell
            self.set_number(0)
            return "break"  #prevent default behavior
        else:
            # if the input is invalid thrn show an error message
            self.status_var.set(f"Invalid input! Only numbers 0-{self.size} are allowed.")
            return "break"  #this si to prevent any non-digit input
    
    
    def change_board_size(self, event=None):
        """Handle board size change"""
        size_str = self.size_var.get()
        if size_str == "3×3":
            self.size = 3
            self.box_size_rows = 1  # 1×1 boxes for 3×3
            self.box_size_cols = 1
        elif size_str == "6×6":
            self.size = 6
            self.box_size_rows = 2  # 2×3 boxes for 6×6
            self.box_size_cols = 3
        else:  # 9×9
            self.size = 9
            self.box_size_rows = 3  # 3×3 boxes for 9×9
            self.box_size_cols = 3
        
        #reset game with new size
        self.new_game()

   
    def new_game(self):
       #### """Generate a new Sudoku puzzle"""
        #stop any ongoing solving
        self.stop_solving()
        
        #generate a new puzzle
        puzzle, solution = self.generate_puzzle()
        
        # Store the boards
        self.current_board = [row[:] for row in puzzle]
        self.original_board = [row[:] for row in puzzle]
        self.solution_board = solution
        
        self.flattened_board = self.flatten_board(self.original_board)
        
        #here we are resetting the board display
        #and the cell entries

        #and reset selection
        self.selected_cell = (-1, -1)
        
        #reset invalid cells
        self.invalid_cells = set()
        
        #reset statistics (FULL RESET)
        self.iterations = 0
        self.elapsed_time = 0.0
        self.memory_used = 0.0
        self.fitness = 0
        self.progress_var.set(0)
        
        self.iterations_var.set("0")
        self.time_var.set("0.00s")
        self.memory_var.set("0.00 MB")
        self.fitness_var.set("N/A")
        
        #reset status
        self.status_var.set("New puzzle loaded")
        
        #create/update the board UI
        self.create_board_ui()
        
        #update the board display
        self.update_board_display()
        
        #forcing the GUI t0 refresh immediately
        self.root.update()

    def generate_puzzle(self):
       ## Generate a Sudoku puzzle of the current size
        #create empty board
        board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        
        #filling diagonal boxes first (these can be filled independently)
        for i in range(0, self.size, max(self.box_size_rows, self.box_size_cols)):
            if i + self.box_size_rows <= self.size and i + self.box_size_cols <= self.size:
                self.fill_box(board, i, i)
        
        #fill the rest using backtracking
        self.solve_board(board)
        
        #then create a copy for the solution
        solution = [row[:] for row in board]
        
        #and remove some numbers to create the puzzle
        cells_to_remove = int(self.size * self.size * 0.6)  #her we are rwemoving about 60% of cells
        
        #then get all cell positions and shuffle them
        positions = [(i, j) for i in range(self.size) for j in range(self.size)]
        random.shuffle(positions)
        
        for i in range(min(cells_to_remove, len(positions))):
            row, col = positions[i]
            board[row][col] = 0
        
        return board, solution
    
    def fill_box(self, board, start_row, start_col):
        """Fill a box with random numbers"""
        nums = list(range(1, self.size + 1))
        random.shuffle(nums)
        
        for i in range(self.box_size_rows):
            for j in range(self.box_size_cols):
                if start_row + i < self.size and start_col + j < self.size:
                    board[start_row + i][start_col + j] = nums.pop()
    
    def is_valid_placement(self, board, row, col, num):
        """Check if placing 'num' at position (row, col) is valid"""
        for x in range(self.size):
            if board[row][x] == num:
                return False
        
        for x in range(self.size):
            if board[x][col] == num:
                return False
        
        box_row, box_col = row - row % self.box_size_rows, col - col % self.box_size_cols
        for i in range(self.box_size_rows):
            for j in range(self.box_size_cols):
                if box_row + i < self.size and box_col + j < self.size:
                    if board[box_row + i][box_col + j] == num:
                        return False
        
        return True
    
    def solve_board(self, board):
       #### Solve the board using backtracking
        for row in range(self.size):
            for col in range(self.size):
                if board[row][col] == 0:
                    for num in range(1, self.size + 1):
                        if self.is_valid_placement(board, row, col, num):
                            board[row][col] = num
                            
                            if self.solve_board(board):
                                return True
                            
                            board[row][col] = 0
                    
                    return False
        
        return True
    
    def flatten_board(self, board):
        #convert 2D board to a flattened string
        return ''.join(str(cell) for row in board for cell in row)
    
    def unflatten_board(self, flattened, size):
        #then convert the flattened string back to a 2D board
        board = []
        for i in range(0, len(flattened), size):
            board.append([int(flattened[i+j]) for j in range(size)])
        return board
    
    def select_cell(self, row, col):
        # this part is for handling cell cselection 
        if not self.solving and self.original_board[row][col] == 0:
            #deselect previous cell
            if self.selected_cell != (-1, -1):
                prev_row, prev_col = self.selected_cell
                box_row, box_col = prev_row // self.box_size_rows, prev_col // self.box_size_cols
                is_even_box = (box_row + box_col) % 2 == 0
                bg_color = COLORS["bg_light"] if is_even_box else COLORS["bg_medium"]
                
                self.cell_entries[prev_row][prev_col].configure(bg=bg_color)
            
            # Select new cell
            self.selected_cell = (row, col)
            
            self.cell_entries[row][col].configure(bg=COLORS["selected"])
            self.cell_entries[row][col].focus_set() 
    
    def set_number(self, num):
        ##set the number in the selected cell
        if self.selected_cell != (-1, -1) and not self.solving:
            row, col = self.selected_cell
            
            #only allow the changing cells that were empty in the original board
            if self.original_board[row][col] == 0:
                #toggle the number if it's already there
                if self.current_board[row][col] == num:
                    self.current_board[row][col] = 0
                    
                    #removing from invalid cells if it was there
                    if (row, col) in self.invalid_cells:
                        self.invalid_cells.remove((row, col))
                else:
                    self.current_board[row][col] = num
                    
                    #then chexking if this placement is valid
                    self.validate_cell(row, col)
                
                #updating the the display
                self.update_board_display()
                
                #keep the focus on the current cell after setting number
                self.cell_entries[row][col].focus_set()
    
    def validate_cell(self, row, col):
     #  here we are checking  if the number in the cell is valid according to Sudoku rules  row, col)
        num = self.current_board[row][col]
        
        #skip empty cells
        if num == 0:
            if (row, col) in self.invalid_cells:
                self.invalid_cells.remove((row, col))
            return True
        
        #then create a temporary board without the current number to check against
        temp_board = [r[:] for r in self.current_board]
        temp_board[row][col] = 0
        
        #aand check if the placement is valid
        is_valid = self.is_valid_placement(temp_board, row, col, num)
        
        #and update invalid cells set
        if not is_valid:
            self.invalid_cells.add((row, col))
            self.status_var.set("Invalid move! Check highlighted cells.")
        else:
            if (row, col) in self.invalid_cells:
                self.invalid_cells.remove((row, col))
            
            #check if there are still any invalid cells
            if not self.invalid_cells:
                self.status_var.set("Valid move!")
        
        return is_valid 
       
    
    def check_solution(self):
        #check if the current board state is valid and complete
        #first we check if the board is complete (like no empty cells)
        for i in range(self.size):
            for j in range(self.size):
                if self.current_board[i][j] == 0:
                    messagebox.showinfo("Incomplete", "The puzzle is not complete yet!")
                    return
        
        #now we check if there are wrong cells (duplicates and stuff)
        if self.invalid_cells:
            messagebox.showwarning("Invalid Solution", 
                                  f"There are {len(self.invalid_cells)} invalid cells. Please correct them!")
            return
        
        #okay now we check everything properly
        is_valid = self.validate_full_board()
        
        if is_valid:
            messagebox.showinfo("Congratulations!", "Your solution is correct!")
            self.status_var.set("Puzzle solved correctly!")
        else:
            messagebox.showwarning("Invalid Solution", 
                                  "Your solution contains errors. Please check the highlighted cells.")
    
    # CHANGED: Updated to use box_size_rows and box_size_cols
    def validate_full_board(self):
        ####validate the entire board and highlight all invalid cells
        self.invalid_cells = set()
        
        #check rows one by one
        for row in range(self.size):
            seen = {}
            for col in range(self.size):
                num = self.current_board[row][col]
                if num != 0:
                    if num in seen:
                        self.invalid_cells.add((row, col))
                        self.invalid_cells.add((row, seen[num]))
                    else:
                        seen[num] = col
        
        #check cols one by one
        for col in range(self.size):
            seen = {}
            for row in range(self.size):
                num = self.current_board[row][col]
                if num != 0:
                    if num in seen:
                        self.invalid_cells.add((row, col))
                        self.invalid_cells.add((seen[num], col))
                    else:
                        seen[num] = row
        
        #check the boxes (like 3x3 boxes in sudoku)
        for box_row in range(0, self.size, self.box_size_rows):
            for box_col in range(0, self.size, self.box_size_cols):
                seen = {}
                for i in range(self.box_size_rows):
                    for j in range(self.box_size_cols):
                        if box_row + i < self.size and box_col + j < self.size:
                            row, col = box_row + i, box_col + j
                            num = self.current_board[row][col]
                            if num != 0:
                                if num in seen:
                                    self.invalid_cells.add((row, col))
                                    prev_row, prev_col = seen[num]
                                    self.invalid_cells.add((prev_row, prev_col))
                                else:
                                    seen[num] = (row, col)
        
         #now update screen to show red cells
        self.update_board_display()
        
        return len(self.invalid_cells) == 0
    
    
    def update_board_display(self):
               #update the board on screen so it shows whatever numbers we have right now
        for i in range(self.size):
            for j in range(self.size):
                cell_value = self.current_board[i][j]
                
                cell_entry = self.cell_entries[i][j]
                
                #put the number inside the box, or leave empty if it's 0
                if cell_value == 0:
                    cell_entry.delete(0, tk.END)
                else:
                    cell_entry.delete(0, tk.END)
                    cell_entry.insert(0, str(cell_value))
                
                #decide background color based on which box it's in
                box_row, box_col = i // self.box_size_rows, j // self.box_size_cols
                is_even_box = (box_row + box_col) % 2 == 0
                base_bg_color = COLORS["bg_light"] if is_even_box else COLORS["bg_medium"]
                
                #now set background if selected or invalid
                if (i, j) == self.selected_cell:
                    cell_entry.configure(bg=COLORS["selected"])
                elif (i, j) in self.invalid_cells:
                    cell_entry.configure(bg=COLORS["invalid"])  #highlight invalid cells (with red)
                else:
                    cell_entry.configure(bg=base_bg_color)
                
                #set the text color and state based on whether it's an original number or a number typed by tthe user
                if self.original_board[i][j] != 0:
                    cell_entry.configure(fg=COLORS["original_cell"], state="disabled")
                else:
                    cell_entry.configure(fg=COLORS["user_cell"], state="normal")

    def solve_puzzle(self):
        #here we start solving the sudoku using the selected method
        if self.solving:
            return #if already solving, don't do anything

      
        self.start_time = time.time()   #store the start time when solving begins
        
        #reset all the counters and stats
        self.iterations = 0
        self.elapsed_time = 0.0
        self.memory_used = 0.0
        self.fitness = 0
        self.progress_var.set(0)
        
        self.iterations_var.set("0")
        self.time_var.set("0.00s")
        self.memory_var.set("0.00 MB")
        self.fitness_var.set("N/A")
        
        # Update status
        self.status_var.set("Solving...")
        
        # Update GUI immediately
        self.root.update()

        #save and update the flattened board with current state
        self.flattened_board = self.flatten_board(self.current_board)

        #set solving flag to true
        self.solving = True

        #disabling the solve button
        self.solve_btn.configure(state=tk.DISABLED)

        #this is to check if the puzzle is already solved before starting the solver
        if self.is_puzzle_already_solved():
            #so if it is already solved, update stats and display
            self.elapsed_time = time.time() - self.start_time
            self.iterations = 1  
            self.progress_var.set(100)
            self.iterations_var.set("1")
            self.time_var.set(f"{self.elapsed_time:.2f}s")
            self.memory_var.set("0.01 MB")  
            self.status_var.set("Puzzle already solved!")
            self.solving = False
            self.solve_btn.configure(state=tk.NORMAL)
            return

        #start solving in a separate thread
        self.solver_thread = threading.Thread(target=self.run_solver)
        self.solver_thread.daemon = True
        self.solver_thread.start()
    
    def is_puzzle_already_solved(self):
        ##check if the puzzle is already solved
        #see if the board is already completed and correct
        for i in range(self.size):
            for j in range(self.size):
                if self.current_board[i][j] == 0:
                    return False #if any empty cell found, not solved yet
        
        return self.validate_full_board() #check if everything is valid
    
    def stop_solving(self):
         #stop the solving process if it's running
        self.solving = False
        if self.solver_thread and self.solver_thread.is_alive():
            #wait for the thread to finish, give it a little time to stop
            self.solver_thread.join(0.1)
        
        self.solve_btn.configure(state=tk.NORMAL) #enable solve button again
    
    def run_solver(self):
        ##Run the selected solver algorithm, (either backtracking or geentic)
        algorithm = self.algo_var.get()
        
        if algorithm == "genetic":
            self.run_genetic_solver()
        else:
            self.run_backtracking_solver()




  
        ##run the genetic algorithm solver with size-optimized parameters
        #solve sudoku using the genetic algorithm method
        #first start timing and memory tracking
    def run_genetic_solver(self):
       ##run the genetic algorithm solver with size-optimized parameters
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # Memory usage in MB
        
        # Calculate puzzle difficulty
        empty_cells = sum(1 for row in self.current_board for cell in row if cell == 0)
        puzzle_difficulty = empty_cells / (self.size * self.size)  
        
        # Set parameters based on puzzle size and difficulty
        if self.size <= 3:
            population_size = 20
            max_generations = 100
            mutation_rate = 0.3
            tournament_size = 2
            stagnation_limit = 10
        elif self.size <= 6:
            population_size = 100
            max_generations = 1000
            mutation_rate = 0.35
            tournament_size = 4
            stagnation_limit = 30
        else:
            population_size = 150
            max_generations = 2000
            mutation_rate = 0.3
            tournament_size = 5
            stagnation_limit = 50

        # Set early termination point depending on puzzle size
        if self.size <= 3:
            early_termination_threshold = int(max_generations * 0.3)  # ~30 iterations
        elif self.size <= 6:
            early_termination_threshold = int(max_generations * 0.5)  # ~500 iterations
        else:
            early_termination_threshold = int(max_generations * 0.75)  # ~1500 iterations
                
        # Initialize population
        population = []
        for _ in range(population_size):
            gnome = self.create_gnome_2d()
            fitness = self.calculate_fitness_2d(gnome)
            population.append((gnome, fitness))
        
        # Sort population by fitness (lower is better)
        population.sort(key=lambda x: x[1])
        
        best_fitness = population[0][1]
        best_solution_ever = population[0][0]
        best_fitness_ever = best_fitness
        stagnation_counter = 0
        
        # Update stats right after starting
        self.iterations = 1
        self.elapsed_time = time.time() - self.start_time
        self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
        self.fitness = population[0][1]
        
        # Update UI with initial stats
        self.root.after(0, lambda: self.update_stats_ui())
        
        # Check if we already found a perfect solution
        perfect_solution_found = False
        if self.is_valid_solution_2d(population[0][0]) and population[0][1] == 0:
            perfect_solution_found = True
            best_solution_ever = population[0][0]
            best_fitness_ever = population[0][1]
        
        # MAIN LOOP - Start the main loop for generations
        for generation in range(1, max_generations + 1):
            if not self.solving:
                break # Stop if solving is stopped
                
            self.iterations = generation
            
            # Update progress bar
            self.progress_var.set(min(99, (generation / max_generations) * 100))
            
            # Update stats (time, memory, fitness)
            self.elapsed_time = time.time() - self.start_time
            self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
            self.fitness = population[0][1]
            
            # Update the UI every 5 generations to keep it smooth
            if generation % 5 == 0: 
                self.root.after(0, lambda: self.update_stats_ui())
        
            # Check for early termination
            if perfect_solution_found and generation >= early_termination_threshold:
                # Add a small random chance to continue even after threshold
                if random.random() > 0.1:  # 90% chance to stop
                    break
            
            # Check for stagnation
            if stagnation_counter >= stagnation_limit:
                acceptable_fitness = self.size // 2  # Scale based on board size
                if population[0][1] <= acceptable_fitness:
                    break

            # Check again if we got a perfect solution
            if not perfect_solution_found and self.is_valid_solution_2d(population[0][0]) and population[0][1] == 0:
                perfect_solution_found = True
                best_solution_ever = population[0][0]
                best_fitness_ever = population[0][1]
    
                self.status_var.set(f"Solution found at iteration {generation}, confirming...")
            
            # Make a new generation
            new_population = []
            
            # Keep the best solutions (elitism)
            elite_count = max(2, self.size // 3)  
            for i in range(min(elite_count, len(population))):
                new_population.append(population[i])
            
            # Fill the rest of the population with offspring
            while len(new_population) < population_size:
                # Tournament selection for parent 1
                tournament1 = random.sample(population, min(tournament_size, len(population)))
                tournament1.sort(key=lambda x: x[1])
                parent1 = tournament1[0][0]
                
                # Tournament selection for parent 2
                tournament2 = random.sample(population, min(tournament_size, len(population)))
                tournament2.sort(key=lambda x: x[1])
                parent2 = tournament2[0][0]
                
                # Create offspring
                child = self.mate_2d(parent1, parent2, mutation_rate)
                child_fitness = self.calculate_fitness_2d(child)
                
                # Add the child to the new population
                new_population.append((child, child_fitness))
            
            # Replace old population with the new one
            population = new_population
            population.sort(key=lambda x: x[1])
            
            # Check for improvement
            if population[0][1] < best_fitness:
                best_fitness = population[0][1]
                stagnation_counter = 0
                
                # Track the best solution ever seen
                if population[0][1] < best_fitness_ever:
                    best_solution_ever = population[0][0]
                    best_fitness_ever = population[0][1]
            else:
                stagnation_counter += 1 # If no improvement, add to stagnation counter
            
            # Add diversity if stuck
            if stagnation_counter >= stagnation_limit // 2:
                diversity_count = population_size // 4
                for i in range(diversity_count):
                    gnome = self.create_gnome_2d()
                    fitness = self.calculate_fitness_2d(gnome)
                    population.append((gnome, fitness))
                
                # Keep only the best ones after adding randomness
                population.sort(key=lambda x: x[1])
                population = population[:population_size]
                stagnation_counter = 0
        
        # Use the best solution found during the entire run
        self.current_board = [row[:] for row in best_solution_ever]  # Deep copy the 2D solution
        self.fitness = best_fitness_ever
        
        # Final stats update
        self.elapsed_time = time.time() - self.start_time
        self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
        self.progress_var.set(100)
        
        # Update status text
        self.status_var.set(f"Puzzle solved in {self.iterations} iterations!")
        
        # Update display
        self.root.after(0, self.update_board_display)
        self.root.after(0, self.update_stats_ui)
        
        # Reset solving state
        self.solving = False
        self.root.after(0, lambda: self.solve_btn.configure(state=tk.NORMAL))




    def update_stats_ui(self):
        #update the statistics UI elements
        self.iterations_var.set(f"{self.iterations:,}") #update how many iterations we did
        self.time_var.set(f"{self.elapsed_time:.2f}s")  #update how much time passed
        self.memory_var.set(f"{self.memory_used:.2f} MB")  #update how much memory we used
        
        #only show fitness value if we are using genetic algorithm
        if self.algo_var.get() == "genetic":
            self.fitness_var.set(f"{self.fitness}")
        else:
            self.fitness_var.set("N/A")
    

     #now run the backtracking solver
    def run_backtracking_solver(self):
        """Run the backtracking algorithm solver using 2D representation"""
        # Start tracking time and memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
        
        # Create a 2D board from the current board
        board_2d = [row[:] for row in self.current_board]
        
        # Update stats immediately before starting
        self.iterations = 0
        self.elapsed_time = time.time() - self.start_time
        self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
        self.root.after(0, lambda: self.update_stats_ui())
        
        # Define the recursive backtrack function
        def backtrack(board_2d):
            if not self.solving:
                return False
                
            self.iterations += 1
            
            # Update UI every 10 moves/iterations
            if self.iterations % 10 == 0:  
                self.elapsed_time = time.time() - self.start_time
                self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
                self.progress_var.set(min(99, (self.iterations / 10000) * 100))
                self.root.after(0, lambda: self.update_stats_ui())
            
            # Find an empty cell
            empty_cell = None
            for row in range(self.size):
                for col in range(self.size):
                    if board_2d[row][col] == 0:
                        empty_cell = (row, col)
                        break
                if empty_cell:
                    break
            
            if empty_cell is None:
                # Board is full (no empty cell found), solution is found
                return True
            
            row, col = empty_cell
            
            for num in range(1, self.size + 1):
                if self.is_valid_2d(board_2d, row, col, num):
                    board_2d[row][col] = num
                    
                    if backtrack(board_2d): # Recursive call
                        return True
                    
                    # If we get here, this path didn't work, so we backtrack
                    board_2d[row][col] = 0
            
            # No solution was found in this branch
            return False
        
        # Start backtracking
        result = backtrack(board_2d)
        
        # After done, update the stats
        self.elapsed_time = time.time() - self.start_time
        self.memory_used = (process.memory_info().rss / (1024 * 1024)) - initial_memory
        
        if self.iterations == 0:
            self.iterations = 1
        
        self.root.after(0, lambda: self.update_stats_ui())
        
        if result and self.solving:
            # Update the current board with the solution
            self.current_board = [row[:] for row in board_2d]
            self.progress_var.set(100)

            self.status_var.set("Puzzle solved!")
            
            self.root.after(0, self.update_board_display)
        
        # Reset solving status
        self.solving = False
        self.root.after(0, lambda: self.solve_btn.configure(state=tk.NORMAL))

    def is_valid_2d(self, board_2d, row, col, num):
        """Check if a move is allowed (valid) in 2D board"""
        # Check row
        for c in range(self.size):
            if board_2d[row][c] == num:
                return False
        
        # Check column
        for r in range(self.size):
            if board_2d[r][col] == num:
                return False
        
        # Check box
        box_row_start = (row // self.box_size_rows) * self.box_size_rows
        box_col_start = (col // self.box_size_cols) * self.box_size_cols
        
        for r in range(box_row_start, box_row_start + self.box_size_rows):
            for c in range(box_col_start, box_col_start + self.box_size_cols):
                if r < self.size and c < self.size:
                    if board_2d[r][c] == num:
                        return False
        
        return True

    # The solve_board and is_valid_placement functions are already using 2D representation
    # so they don't need to be changed

    def solve_board(self, board):
        """Solve the board using backtracking"""
        for row in range(self.size):
            for col in range(self.size):
                if board[row][col] == 0:
                    for num in range(1, self.size + 1):
                        if self.is_valid_placement(board, row, col, num):
                            board[row][col] = num
                            
                            if self.solve_board(board):
                                return True
                            
                            board[row][col] = 0
                    
                    return False
        
        return True

    def is_valid_placement(self, board, row, col, num):
        """Check if placing 'num' at position (row, col) is valid"""
        # Check row
        for x in range(self.size):
            if board[row][x] == num:
                return False
        
        # Check column
        for x in range(self.size):
            if board[x][col] == num:
                return False
        
        # Check box
        box_row, box_col = row - row % self.box_size_rows, col - col % self.box_size_cols
        for i in range(self.box_size_rows):
            for j in range(self.box_size_cols):
                if box_row + i < self.size and box_col + j < self.size:
                    if board[box_row + i][box_col + j] == num:
                        return False
        
        return True
    
    def create_gnome_2d(self):
        """Create a chromosome (candidate solution) for genetic algorithm using 2D representation"""
        # Start with a copy of the current board
        board_2d = [row[:] for row in self.current_board]
        
        # First try to fill easy cells that have only 1 valid number
        progress = True
        while progress:
            progress = False
            for row in range(self.size):
                for col in range(self.size):
                    if board_2d[row][col] == 0:  # Only empty cells
                        valid_numbers = self.get_valid_numbers(board_2d, row, col)
                        if len(valid_numbers) == 1:
                            board_2d[row][col] = valid_numbers[0]
                            progress = True
        
        # Fill the rest randomly but valid where possible
        for row in range(self.size):
            for col in range(self.size):
                if board_2d[row][col] == 0: 
                    valid_numbers = self.get_valid_numbers(board_2d, row, col)
                    
                    if valid_numbers:
                        board_2d[row][col] = random.choice(valid_numbers)
                    else:
                        board_2d[row][col] = random.randint(1, self.size)
        
        return board_2d

    def get_valid_numbers(self, board_2d, row, col):
        """Find what numbers can go in this specific position on the 2D board"""
        used_numbers = set()
        
        # Check row - simply iterate through all columns in the current row
        for c in range(self.size):
            used_numbers.add(board_2d[row][c])
        
        # Check column - iterate through all rows in the current column
        for r in range(self.size):
            used_numbers.add(board_2d[r][col])
        
        # Check box - find the top-left corner of the box containing this cell
        box_row_start = (row // self.box_size_rows) * self.box_size_rows
        box_col_start = (col // self.box_size_cols) * self.box_size_cols
        
        # Iterate through all cells in the box
        for r in range(box_row_start, box_row_start + self.box_size_rows):
            for c in range(box_col_start, box_col_start + self.box_size_cols):
                if r < self.size and c < self.size:
                    used_numbers.add(board_2d[r][c])
        
        # Return available numbers (numbers 1 to size that are not in used_numbers)
        return [num for num in range(1, self.size + 1) if num not in used_numbers]

    def calculate_fitness_2d(self, board_2d):
        """Calculate fitness score for a 2D board (lower = better)"""
        fitness = 0
        
        # Penalize empty cells
        for row in range(self.size):
            for col in range(self.size):
                if board_2d[row][col] == 0:
                    fitness += 10

        # Check rows for duplicates
        for row in range(self.size):
            seen = set()
            for col in range(self.size):
                value = board_2d[row][col]
                if value != 0:
                    if value in seen:
                        fitness += 1
                    seen.add(value)
        
        # Check columns for duplicates
        for col in range(self.size):
            seen = set()
            for row in range(self.size):
                value = board_2d[row][col]
                if value != 0:
                    if value in seen:
                        fitness += 1
                    seen.add(value)
        
        # Check boxes for duplicates
        for box_row in range(0, self.size, self.box_size_rows):
            for box_col in range(0, self.size, self.box_size_cols):
                seen = set()
                for row in range(box_row, box_row + self.box_size_rows):
                    for col in range(box_col, box_col + self.box_size_cols):
                        if row < self.size and col < self.size:
                            value = board_2d[row][col]
                            if value != 0:
                                if value in seen:
                                    fitness += 1
                                seen.add(value)
        
        # Penalize changes to original cells
        for row in range(self.size):
            for col in range(self.size):
                if self.original_board[row][col] != 0 and board_2d[row][col] != self.original_board[row][col]:
                    fitness += 5
        
        return fitness

    def mate_2d(self, parent1, parent2, mutation_rate=0.2):
        """Combine two parent solutions to create a child solution using 2D representation"""
        # Create an empty child board
        child = [[0 for _ in range(self.size)] for _ in range(self.size)]
        
        # Fill in the original clues first
        for row in range(self.size):
            for col in range(self.size):
                if self.original_board[row][col] != 0:
                    # Keep original clue
                    child[row][col] = self.original_board[row][col]
        
        # Fill in the rest of the cells
        for row in range(self.size):
            for col in range(self.size):
                if child[row][col] == 0:  # Skip cells that already have original clues
                    # Decide whether to mutate
                    if random.random() < mutation_rate:
                        # Try to find valid numbers for this position
                        valid_numbers = self.get_valid_numbers(child, row, col)
                        
                        if valid_numbers:
                            child[row][col] = random.choice(valid_numbers)
                        else:
                            # If no valid numbers, choose from parents or random
                            p1_val = parent1[row][col] if parent1[row][col] != 0 else random.randint(1, self.size)
                            p2_val = parent2[row][col] if parent2[row][col] != 0 else random.randint(1, self.size)
                            child[row][col] = p1_val if random.random() < 0.5 else p2_val
                    else:
                        # Choose from parents (never allow zeros)
                        p1_val = parent1[row][col] if parent1[row][col] != 0 else random.randint(1, self.size)
                        p2_val = parent2[row][col] if parent2[row][col] != 0 else random.randint(1, self.size)
                        child[row][col] = p1_val if random.random() < 0.5 else p2_val
        
        # Make sure no zeros are left in the child
        for row in range(self.size):
            for col in range(self.size):
                if child[row][col] == 0:
                    valid_numbers = self.get_valid_numbers(child, row, col)
                    if valid_numbers:
                        child[row][col] = random.choice(valid_numbers)
                    else:
                        child[row][col] = random.randint(1, self.size)
        
        return child

    def is_valid_solution_2d(self, board_2d):
        """Check if a 2D solution is valid (no duplicates in rows, columns, boxes)"""
        # Check for any zeros (incomplete solution)
        for row in range(self.size):
            for col in range(self.size):
                if board_2d[row][col] == 0:
                    return False
        
        # Check rows
        for row in range(self.size):
            if len(set(board_2d[row])) != self.size:
                return False
        
        # Check columns
        for col in range(self.size):
            column_values = [board_2d[row][col] for row in range(self.size)]
            if len(set(column_values)) != self.size:
                return False
        
        # Check boxes
        for box_row in range(0, self.size, self.box_size_rows):
            for box_col in range(0, self.size, self.box_size_cols):
                box_values = []
                for row in range(box_row, box_row + self.box_size_rows):
                    for col in range(box_col, box_col + self.box_size_cols):
                        if row < self.size and col < self.size:
                            box_values.append(board_2d[row][col])
                if len(set(box_values)) != self.size:
                    return False
        
        return True
    
    def update_stats_display(self):
       #keep showing updated stats on screen
        if self.solving:
            #update statistics labels
            self.iterations_var.set(f"{self.iterations:,}")
            self.time_var.set(f"{self.elapsed_time:.2f}s")
            self.memory_var.set(f"{self.memory_used:.2f} MB")
            
            if self.algo_var.get() == "genetic":
                self.fitness_var.set(f"{self.fitness}")
                self.fitness_label.grid()
            else:
                self.fitness_var.set("N/A")
                self.fitness_label.grid()
        
        self.root.after(20, self.update_stats_display)  #update every 20 milliseconds


# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
   #set window title
    root.title("Modern Sudoku Solver")
    
    #set minimum size for window
    root.minsize(800, 600)
    
    #make window centered on screen
    window_width = 900
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = SudokuSolver(root)
    root.mainloop()