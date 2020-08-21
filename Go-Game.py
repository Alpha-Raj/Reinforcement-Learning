import sys
import time
import random
import timeit
import math
import argparse
from collections import Counter
from copy import deepcopy
import pickle

BOARD_ROWS = 5
BOARD_COLS = 5


# from .read import *
# from .write import writeNextInput


def writeOutput(result, path="output.txt"):
    res = ""
    if result == "PASS":
        res = "PASS"
    else:
        res += str(result[0]) + ',' + str(result[1])

    with open(path, 'w') as f:
        f.write(res)


def writePass(path="output.txt"):
    with open(path, 'w') as f:
        f.write("PASS")


def writeNextInput(piece_type, previous_board, board, path="input.txt"):
    res = ""
    res += str(piece_type) + "\n"
    for item in previous_board:
        res += "".join([str(x) for x in item])
        res += "\n"

    for item in board:
        res += "".join([str(x) for x in item])
        res += "\n"

    with open(path, 'w') as f:
        f.write(res[:-1]);


def readInput(n, path="input.txt"):
    with open(path, 'r') as f:
        lines = f.readlines()

        piece_type = int(lines[0])

        previous_board = [[int(x) for x in line.rstrip('\n')] for line in lines[1:n + 1]]
        board = [[int(x) for x in line.rstrip('\n')] for line in lines[n + 1: 2 * n + 1]]

        return piece_type, previous_board, board


def readOutput(path="output.txt"):
    with open(path, 'r') as f:
        position = f.readline().strip().split(',')

        if position[0] == "PASS":
            return "PASS", -1, -1

        x = int(position[0])
        y = int(position[1])

    return "MOVE", x, y


class GO:
    def __init__(self, n):
        """
        Go game.

        :param n: size of the board n*n
        """
        self.size = n
        # self.previous_board = None # Store the previous board
        self.X_move = True  # X chess plays first
        self.died_pieces = []  # Intialize died pieces to be empty
        self.n_move = 0  # Trace the number of moves
        self.max_move = n * n - 1  # The max movement of a Go game
        self.komi = n / 2  # Komi rule
        self.verbose = False  # Verbose only when there is a manual player

    def init_board(self, n):
        '''
        Initialize a board with size n*n.

        :param n: width and height of the board.
        :return: None.
        '''
        board = [[0 for x in range(n)] for y in range(n)]  # Empty space marked as 0
        # 'X' pieces marked as 1
        # 'O' pieces marked as 2
        self.board = board
        self.previous_board = deepcopy(board)
        self.n_move = 0

    def set_board(self, piece_type, previous_board, board):
        '''
        Initialize board status.
        :param previous_board: previous board state.
        :param board: current board state.
        :return: None.
        '''

        # 'X' pieces marked as 1
        # 'O' pieces marked as 2

        for i in range(self.size):
            for j in range(self.size):
                if previous_board[i][j] == piece_type and board[i][j] != piece_type:
                    self.died_pieces.append((i, j))

        # self.piece_type = piece_type
        self.previous_board = previous_board
        self.board = board

    def compare_board(self, board1, board2):
        for i in range(self.size):
            for j in range(self.size):
                if board1[i][j] != board2[i][j]:
                    return False
        return True

    def copy_board(self):
        '''
        Copy the current board for potential testing.

        :param: None.
        :return: the copied board instance.
        '''
        return deepcopy(self)

    def detect_neighbor(self, i, j):
        '''
        Detect all the neighbors of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the neighbors row and column (row, column) of position (i, j).
        '''
        board = self.board
        neighbors = []
        # Detect borders and add neighbor coordinates
        if i > 0: neighbors.append((i - 1, j))
        if i < len(board) - 1: neighbors.append((i + 1, j))
        if j > 0: neighbors.append((i, j - 1))
        if j < len(board) - 1: neighbors.append((i, j + 1))
        return neighbors

    def detect_neighbor_ally(self, i, j):
        '''
        Detect the neighbor allies of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the neighbored allies row and column (row, column) of position (i, j).
        '''
        board = self.board
        neighbors = self.detect_neighbor(i, j)  # Detect neighbors
        group_allies = []
        # Iterate through neighbors
        for piece in neighbors:
            # Add to allies list if having the same color
            if board[piece[0]][piece[1]] == board[i][j]:
                group_allies.append(piece)
        return group_allies

    def ally_dfs(self, i, j):
        '''
        Using DFS to search for all allies of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the all allies row and column (row, column) of position (i, j).
        '''
        stack = [(i, j)]  # stack for DFS serach
        ally_members = []  # record allies positions during the search
        while stack:
            piece = stack.pop()
            ally_members.append(piece)
            neighbor_allies = self.detect_neighbor_ally(piece[0], piece[1])
            for ally in neighbor_allies:
                if ally not in stack and ally not in ally_members:
                    stack.append(ally)
        return ally_members

    def find_liberty(self, i, j):
        '''
        Find liberty of a given stone. If a group of allied stones has no liberty, they all die.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: boolean indicating whether the given stone still has liberty.
        '''
        board = self.board
        ally_members = self.ally_dfs(i, j)
        for member in ally_members:
            neighbors = self.detect_neighbor(member[0], member[1])
            for piece in neighbors:
                # If there is empty space around a piece, it has liberty
                if board[piece[0]][piece[1]] == 0:
                    return True
        # If none of the pieces in a allied group has an empty space, it has no liberty
        return False

    def find_died_pieces(self, piece_type):
        '''
        Find the died stones that has no liberty in the board for a given piece type.

        :param piece_type: 1('X') or 2('O').
        :return: a list containing the dead pieces row and column(row, column).
        '''
        board = self.board
        died_pieces = []

        for i in range(len(board)):
            for j in range(len(board)):
                # Check if there is a piece at this position:
                if board[i][j] == piece_type:
                    # The piece die if it has no liberty
                    if not self.find_liberty(i, j):
                        died_pieces.append((i, j))
        return died_pieces

    def remove_died_pieces(self, piece_type):
        '''
        Remove the dead stones in the board.

        :param piece_type: 1('X') or 2('O').
        :return: locations of dead pieces.
        '''

        died_pieces = self.find_died_pieces(piece_type)
        if not died_pieces: return []
        self.remove_certain_pieces(died_pieces)
        return died_pieces

    def remove_certain_pieces(self, positions):
        '''
        Remove the stones of certain locations.

        :param positions: a list containing the pieces to be removed row and column(row, column)
        :return: None.
        '''
        board = self.board
        for piece in positions:
            board[piece[0]][piece[1]] = 0
        self.update_board(board)

    def place_chess(self, i, j, piece_type):
        '''
        Place a chess stone in the board.

        :param i: row number of the board.
        :param j: column number of the board.
        :param piece_type: 1('X') or 2('O').
        :return: boolean indicating whether the placement is valid.
        '''
        board = self.board

        valid_place = self.valid_place_check(i, j, piece_type)
        if not valid_place:
            return False
        self.previous_board = deepcopy(board)
        board[i][j] = piece_type
        self.update_board(board)
        # Remove the following line for HW2 CS561 S2020
        # self.n_move += 1
        return True

    def valid_place_check(self, i, j, piece_type, test_check=False):
        '''
        Check whether a placement is valid.

        :param i: row number of the board.
        :param j: column number of the board.
        :param piece_type: 1(white piece) or 2(black piece).
        :param test_check: boolean if it's a test check.
        :return: boolean indicating whether the placement is valid.
        '''
        board = self.board
        verbose = self.verbose
        if test_check:
            verbose = False

        # Check if the place is in the board range
        if not (i >= 0 and i < len(board)):
            if verbose:
                print(('GO:Invalid placement. row should be in the range 1 to {}.').format(len(board) - 1))
            return False
        if not (j >= 0 and j < len(board)):
            if verbose:
                print(('GO:Invalid placement. column should be in the range 1 to {}.').format(len(board) - 1))
            return False

        # Check if the place already has a piece
        if board[i][j] != 0:
            if verbose:
                print('GO:Invalid placement. There is already a chess in this position.')
            return False

        # Copy the board for testing
        test_go = self.copy_board()
        test_board = test_go.board

        # Check if the place has liberty
        test_board[i][j] = piece_type
        test_go.update_board(test_board)
        if test_go.find_liberty(i, j):
            return True

        # If not, remove the died pieces of opponent and check again
        test_go.remove_died_pieces(3 - piece_type)
        if not test_go.find_liberty(i, j):
            if verbose:
                print('GO:Invalid placement. No liberty found in this position.')
            return False

        # Check special case: repeat placement causing the repeat board state (KO rule)
        else:
            if self.died_pieces and self.compare_board(self.previous_board, test_go.board):
                if verbose:
                    print('GO:Invalid placement. A repeat move not permitted by the KO rule.')
                return False
        return True

    def update_board(self, new_board):
        '''
        Update the board with new_board

        :param new_board: new board.
        :return: None.
        '''
        self.board = new_board

    def visualize_board(self):
        '''
        Visualize the board.

        :return: None
        '''

        board = self.board
        print('-' * len(board) * 2)
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j] == 0:
                    print('-', end=' ')
                elif board[i][j] == 1:
                    print('X', end=' ')
                else:
                    print('O', end=' ')
            print()
        print('-' * len(board) * 2)

    def game_end(self, piece_type, action="MOVE"):
        '''
        Check if the game should end.

        :param piece_type: 1('X') or 2('O').
        :param action: "MOVE" or "PASS".
        :return: boolean indicating whether the game should end.
        '''

        # Case 1: max move reached
        if self.n_move >= self.max_move:
            return True
        # Case 2: two players all pass the move.
        if self.compare_board(self.previous_board, self.board) and action == "PASS":
            return True
        return False

    def score(self, piece_type):
        '''
        Get score of a player by counting the number of stones.

        :param piece_type: 1('X') or 2('O').
        :return: boolean indicating whether the game should end.
        '''

        board = self.board
        cnt = 0
        for i in range(self.size):
            for j in range(self.size):
                if board[i][j] == piece_type:
                    cnt += 1
        return cnt

    def judge_winner(self):
        '''
        Judge the winner of the game by number of pieces for each player.

        :param: None.
        :return: piece type of winner of the game (0 if it's a tie).
        '''

        cnt_1 = self.score(1)
        cnt_2 = self.score(2)
        if cnt_1 > cnt_2 + self.komi:
            return 1
        elif cnt_1 < cnt_2 + self.komi:
            return 2
        else:
            return 0

    def play(self, player1, player2, verbose=False):
        '''
        The game starts!

        :param player1: Player instance.
        :param player2: Player instance.
        :param verbose: whether print input hint and error information
        :return: piece type of winner of the game (0 if it's a tie).
        '''
        self.init_board(self.size)
        # Print input hints and error message if there is a manual player
        if player1.type == 'manual' or player2.type == 'manual':
            self.verbose = True
                    # print('----------Input "exit" to exit the program----------')
                    # print('X stands for black chess, O stands for white chess.')
                    # self.visualize_board()

        verbose = self.verbose
        # Game starts!
        while 1:
            piece_type = 1 if self.X_move else 2

            # Judge if the game should end
            if self.game_end(piece_type):
                result = self.judge_winner()
                if verbose:
                    #                     print('Game ended.')
                    if result == 0:
                        #                         print('The game is a tie.')
                        player1.feedReward(0.5)
                        player2.feedReward(0.1)
                    elif result == 1:
                        #                         print("Reward to Player 1")
                        player1.feedReward(1)
                        player2.feedReward(0)
                    elif result == 2:
                        #                         print("Reward to Player 2")
                        player1.feedReward(0)
                        player2.feedReward(1)

                #                     print('The winner is {}'.format('X' if result == 1 else 'O'))
                return result

            if verbose:
                player = "X" if piece_type == 1 else "O"
            #                 print(player + " makes move...")

            # Game continues
            if piece_type == 1:
                action = player1.get_input()
            else:
                action = player2.get_input()

            if verbose:
                player = "X" if piece_type == 1 else "O"
                # print(action)

            if action != "PASS":
                # If invalid input, continue the loop. Else it places a chess on the board.
                if not self.place_chess(action[0], action[1], piece_type):
                    if verbose:
                        self.visualize_board()
                    continue
                self.died_pieces = self.remove_died_pieces(3 - piece_type)  # Remove the dead pieces of opponent
            else:
                #                 print("Move is Passed by :", piece_type)
                self.previous_board = deepcopy(self.board)

            if verbose:
                self.visualize_board()  # Visualize the board again
                # print()
            player1.board = deepcopy(self.board)
            player1.previous_board = deepcopy(self.board)
            player2.board = deepcopy(self.board)
            player2.previous_board = deepcopy(self.board)
            if piece_type is 1:
                player1.addState()
            else:
                player2.addState()
            self.n_move += 1
            self.X_move = not self.X_move  # Players take turn


def judge(n_move, verbose=False):
    """This function is responsible to check if we have a winner after 24 moves"""
    N = 5

    piece_type, previous_board, board = readInput(N)
    go = GO(N)
    go.verbose = verbose
    go.set_board(piece_type, previous_board, board)
    go.n_move = n_move
    try:
        action, x, y = readOutput()
    except:
        print("output.txt not found or invalid format")
        sys.exit(3 - piece_type)

    if action == "MOVE":
        if not go.place_chess(x, y, piece_type):
            print('Game end.')
            print('The winner is {}'.format('X' if 3 - piece_type == 1 else 'O'))
            sys.exit(3 - piece_type)

        go.died_pieces = go.remove_died_pieces(3 - piece_type)

    if verbose:
        go.visualize_board()
        print()

    if go.game_end(piece_type, action):
        result = go.judge_winner()
        if verbose:
            print('Game end.')
            if result == 0:
                print('The game is a tie.')
            else:
                print('The winner is {}'.format('X' if result == 1 else 'O'))
        sys.exit(result)

    piece_type = 2 if piece_type == 1 else 1

    if action == "PASS":
        go.previous_board = go.board
    writeNextInput(piece_type, go.previous_board, go.board)

    sys.exit(0)


class Player:
    def __init__(self, name, typ, symbol, exp_rate=0.59):
        self.name = name
        self.size = 5
        self.previous_board = [[0 for x in range(BOARD_ROWS)] for y in range(BOARD_COLS)]  # Empty space marked as 0
        self.board = [[0 for x in range(BOARD_ROWS)] for y in range(BOARD_COLS)]  # Empty space marked as 0
        self.type = typ
        self.died_pieces = []
        self.states = []  # record all positions taken
        self.lr = 0.7
        self.playerSymbol = symbol
        self.exp_rate = exp_rate
        self.decay_gamma = 0.9
        self.verbose = True  # Verbose only when there is a manual player
        self.states_value = {}  # state -> value

    # def __de

    def reset(self):
        self.previous_board = [[0 for x in range(BOARD_ROWS)] for y in range(BOARD_COLS)]  # Empty space marked as 0
        self.board = [[0 for x in range(BOARD_ROWS)] for y in range(BOARD_COLS)]  # Empty space marked as 0
        self.died_pieces = []
        self.states = []  # record all positions taken

    def getHash(self, board):
        hash_board = ""
        for i in board:
            for j in i:
                hash_board += str(j)
        return hash_board

    def feedReward(self, reward):
        """THis function is responsible to reward the gameplaying agents after a win/loss"""
        for st in reversed(self.states):
            if self.states_value.get(st) is None:
                self.states_value[st] = 0
            self.states_value[st] += self.lr * (self.decay_gamma * reward - self.states_value[st])
            reward = self.states_value[st]

    def chooseAction(self, positions):
        if random.uniform(0, 1) <= self.exp_rate:
            # take random action
            action = random.choice(positions)
            return action
        else:
            value_max = -999
            for p in positions:
                next_board = deepcopy(self.board)
                next_board[p[0]][p[1]] = self.playerSymbol
                next_boardHash = self.getHash(next_board)
                value = 0 if self.states_value.get(next_boardHash) is None else self.states_value.get(next_boardHash)
                # print("value", value)
                if value >= value_max:
                    value_max = value
                    action = p
        # print("{} takes action {}".format(self.name, action))
        return action

    def get_input(self):
        positions = self.availablePositions()
        if len(positions) is 0:
            print("Zero Positions Returned!")
        actions = []
        for position in positions:
            if self.valid_place_check(position[0], position[1], self.playerSymbol):
                actions.append(position)

        if len(actions) is 0:
            # print("No Actions to make! Return PAss")
            return "PASS"
        action = self.chooseAction(positions=actions)
        return action

    def addState(self):
        self.states.append(self.getHash(self.board))

    def copy_board(self):
        '''
        Copy the current board for potential testing.

        :param: None.
        :return: the copied board instance.
        '''
        return deepcopy(self)

    def update_board(self, new_board):
        '''
        Update the board with new_board

        :param new_board: new board.
        :return: None.
        '''
        self.board = new_board

    def detect_neighbor(self, i, j):
        '''
        Detect all the neighbors of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the neighbors row and column (row, column) of position (i, j).
        '''
        board = self.board
        neighbors = []
        # Detect borders and add neighbor coordinates
        if i > 0: neighbors.append((i - 1, j))
        if i < len(board) - 1: neighbors.append((i + 1, j))
        if j > 0: neighbors.append((i, j - 1))
        if j < len(board) - 1: neighbors.append((i, j + 1))
        return neighbors

    def detect_neighbor_ally(self, i, j):
        '''
        Detect the neighbor allies of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the neighbored allies row and column (row, column) of position (i, j).
        '''
        board = self.board
        neighbors = self.detect_neighbor(i, j)  # Detect neighbors
        group_allies = []
        # Iterate through neighbors
        for piece in neighbors:
            # Add to allies list if having the same color
            if board[piece[0]][piece[1]] == board[i][j]:
                group_allies.append(piece)
        return group_allies

    def ally_dfs(self, i, j):
        '''
        Using DFS to search for all allies of a given stone.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: a list containing the all allies row and column (row, column) of position (i, j).
        '''
        stack = [(i, j)]  # stack for DFS serach
        ally_members = []  # record allies positions during the search
        while stack:
            piece = stack.pop()
            ally_members.append(piece)
            neighbor_allies = self.detect_neighbor_ally(piece[0], piece[1])
            for ally in neighbor_allies:
                if ally not in stack and ally not in ally_members:
                    stack.append(ally)
        return ally_members

    def find_liberty(self, i, j):
        '''
        Find liberty of a given stone. If a group of allied stones has no liberty, they all die.

        :param i: row number of the board.
        :param j: column number of the board.
        :return: boolean indicating whether the given stone still has liberty.
        '''
        board = self.board
        ally_members = self.ally_dfs(i, j)
        for member in ally_members:
            neighbors = self.detect_neighbor(member[0], member[1])
            for piece in neighbors:
                # If there is empty space around a piece, it has liberty
                if board[piece[0]][piece[1]] == 0:
                    return True
        # If none of the pieces in a allied group has an empty space, it has no liberty
        return False

    def compare_board(self, board1, board2):
        for i in range(self.size):
            for j in range(self.size):
                if board1[i][j] != board2[i][j]:
                    return False
        return True

    def find_died_pieces(self, piece_type):
        '''
        Find the died stones that has no liberty in the board for a given piece type.

        :param piece_type: 1('X') or 2('O').
        :return: a list containing the dead pieces row and column(row, column).
        '''
        board = self.board
        died_pieces = []

        for i in range(len(board)):
            for j in range(len(board)):
                # Check if there is a piece at this position:
                if board[i][j] == piece_type:
                    # The piece die if it has no liberty
                    if not self.find_liberty(i, j):
                        died_pieces.append((i, j))
        return died_pieces

    def remove_died_pieces(self, piece_type):
        '''
        Remove the dead stones in the board.

        :param piece_type: 1('X') or 2('O').
        :return: locations of dead pieces.
        '''

        died_pieces = self.find_died_pieces(piece_type)
        if not died_pieces: return []
        self.remove_certain_pieces(died_pieces)
        return died_pieces

    def remove_certain_pieces(self, positions):
        '''
        Remove the stones of certain locations.

        :param positions: a list containing the pieces to be removed row and column(row, column)
        :return: None.
        '''
        board = self.board
        for piece in positions:
            board[piece[0]][piece[1]] = 0
        self.update_board(board)

    def valid_place_check(self, i, j, piece_type, test_check=False):
        '''
        Check whether a placement is valid.

        :param i: row number of the board.
        :param j: column number of the board.
        :param piece_type: 1(white piece) or 2(black piece).
        :param test_check: boolean if it's a test check.
        :return: boolean indicating whether the placement is valid.
        '''
        board = self.board
        verbose = self.verbose
        if test_check:
            verbose = False

        # Copy the board for testing

        test_go = Player(name=self.name, typ=self.type, symbol=self.playerSymbol)
        test_go.board = deepcopy(self.board)
        test_board = test_go.board

        # Check if the place has liberty
        test_board[i][j] = piece_type
        test_go.update_board(test_board)
        if test_go.find_liberty(i, j):
            return True

        # If not, remove the died pieces of opponent and check again
        test_go.remove_died_pieces(3 - piece_type)
        if not test_go.find_liberty(i, j):
            if verbose:
                print('Invalid placement. No liberty found in this position.')
            return False

        # Check special case: repeat placement causing the repeat board state (KO rule)
        else:
            if self.died_pieces and self.compare_board(self.previous_board, test_go.board):
                if verbose:
                    print('Invalid placement. A repeat move not permitted by the KO rule.')
                return False
        return True

    def availablePositions(self):
        positions = []
        bit = True
        target = 1 if self.playerSymbol == 2 else 2
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                if self.board[i][j] == 0:
                    if 0 < i < BOARD_ROWS - 1 and 0 < j < BOARD_COLS - 1:
                        if self.board[i - 1][j] == target and self.board[i + 1][j] == target and self.board[
                            i][j + 1] == target and self.board[i][j - 1] == target:
                            bit = False
                    elif j == 0 and i == 0:
                        if self.board[i][j + 1] == target and self.board[i + 1][j] == target:
                            bit = False
                    elif i == 0 and 0 < j < BOARD_COLS - 1:
                        if self.board[i][j - 1] == target and self.board[i][j + 1] == target and self.board[
                            i + 1][j] == target:
                            bit = False
                    elif i == 0 and j == BOARD_COLS - 1:
                        if self.board[i][j - 1] == target and self.board[i + 1][j] == target:
                            bit = False
                    elif j == BOARD_COLS - 1 and 0 < i < BOARD_ROWS - 1:
                        if self.board[i - 1][j] == target and self.board[i][j - 1] == target and self.board[
                            i + 1][j] == target:
                            bit = False
                    elif i == BOARD_ROWS - 1 and j == BOARD_COLS - 1:
                        if self.board[i - 1][j] == target and self.board[i][j - 1] == target:
                            bit = False
                    elif i == BOARD_ROWS - 1 and 0 < j < BOARD_COLS - 1:
                        if self.board[i][j - 1] == target and self.board[i][j + 1] == target and self.board[
                            i - 1][j] == target:
                            bit = False
                    elif i == BOARD_ROWS - 1 and j == 0:
                        if self.board[i][j + 1] == target and self.board[i - 1][j] == target:
                            bit = False
                    elif j == 0 and 0 < i < BOARD_ROWS - 1:
                        if self.board[i - 1][j] == target and self.board[i + 1][j] == target and self.board[
                            i][j + 1] == target:
                            bit = False
                    if bit:
                        positions.append((i, j))  # need to be tuple
                    bit = True
        if len(positions) is 0:
            print("Zero Positions Returned!")
        return positions

    def savePolicy(self, i):
        fw = open(str(i) + 'run_policy_' + str(self.name), 'wb')
        pickle.dump(self.states_value, fw)
        fw.close()

    def loadPolicy(self, file):
        fr = open(file, 'rb')
        self.states_value = pickle.load(fr)
        fr.close()


if __name__ == "__main__":
    go = GO(5)
    num_games = 7500000  # Total number of games you want you agents to Play.
    save_policy_after = 2500000  # After how many games do you want to save the policy.
    learning_rate_decay = 500000  # After how many games do you want your learning rate to decay.
    player1 = Player(name="player1", typ="manual", symbol=1)
    player2 = Player(name="player2", typ="manual", symbol=2)
    Start_time = time.time()

    # Below Code should be used when you already have your policy.

    # player1.loadPolicy('Name-of-policy-file')
    # print("Player 1 load Policy ::", time.time() - Start_time)
    #
    # p2_start = time.time()
    # player2.loadPolicy('Name-of-policy-file')
    # print("Player 2 load Policy ::", time.time() - p2_start)
    # print("Length of state_value for player 1:", len(player1.states_value))
    # print("Length of state_value for player 2:", len(player2.states_value))

    for i in range(num_games):
        go.play(player1=player1, player2=player2)
        player1.reset()
        player2.reset()
        if i % save_policy_after == 0:
            print("Rounds {}".format(i))
            player1.savePolicy(i + save_policy_after)
            player2.savePolicy(i + save_policy_after)
        if i % learning_rate_decay == 0:
            player1.exp_rate = player1.exp_rate * 0.9
            player2.exp_rate = player2.exp_rate * 0.9
            print("Current Exp Rate:-", player1.exp_rate)
    print("Program Complete")
    print("Length of state_value for player 1:", len(player1.states_value))
    print("Length of state_value for player 2:", len(player2.states_value))
    player1.savePolicy(i=num_games)
    player2.savePolicy(i=num_games)
    print("Total Execution time ::", time.time() - Start_time)

    # judge(args.move, args.verbose)
