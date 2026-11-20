"""Board primitives adapted from Renaud Gaudron's connect-4-game-engine.

Source: https://github.com/RenaudGaudron/connect-4-game-engine/blob/main/src/connect4_engine/board.py
See LICENSE in this directory.
"""

EMPTY = 0
PLAYER_ONE = 1
PLAYER_TWO = 2


def create_board(row_count, column_count):
    return [[EMPTY for _ in range(column_count)] for _ in range(row_count)]


def is_valid_location(board, column, row_count):
    if column < 0 or column >= len(board[0]):
        return False
    return board[row_count - 1][column] == EMPTY


def get_next_open_row(board, column, row_count):
    if column < 0 or column >= len(board[0]):
        return None
    for row in range(row_count):
        if board[row][column] == EMPTY:
            return row
    return None


def drop_piece(board, row, column, piece):
    board[row][column] = piece


def get_valid_locations(board, row_count, column_count):
    return [column for column in range(column_count) if is_valid_location(board, column, row_count)]


def winning_move(board, piece, row_count, column_count, window_length):
    for row in range(row_count):
        for column in range(column_count - window_length + 1):
            if all(cell == piece for cell in board[row][column:column + window_length]):
                return True
    for column in range(column_count):
        for row in range(row_count - window_length + 1):
            if all(board[row + offset][column] == piece for offset in range(window_length)):
                return True
    for row in range(row_count - window_length + 1):
        for column in range(column_count - window_length + 1):
            if all(board[row + offset][column + offset] == piece for offset in range(window_length)):
                return True
    for row in range(window_length - 1, row_count):
        for column in range(column_count - window_length + 1):
            if all(board[row - offset][column + offset] == piece for offset in range(window_length)):
                return True
    return False


def detect_winner(board, row_count, column_count, window_length):
    if winning_move(board, PLAYER_ONE, row_count, column_count, window_length):
        return PLAYER_ONE, False
    if winning_move(board, PLAYER_TWO, row_count, column_count, window_length):
        return PLAYER_TWO, False
    return 0, not any(cell == EMPTY for row in board for cell in row)
