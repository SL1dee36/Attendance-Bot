# game/tictactoe.py

def create_board():
    return [[" " for _ in range(3)] for _ in range(3)]

def format_board(board, room_code):
    from telebot import types  # Import types here
    markup = types.InlineKeyboardMarkup(row_width=3)
    for row_index, row in enumerate(board):
        button_row = []
        for col_index, cell in enumerate(row):
            callback_data = f"move:{room_code}:{row_index}:{col_index}"
            button_row.append(types.InlineKeyboardButton(text=cell, callback_data=callback_data))
        markup.row(*button_row)
    return markup

def check_win(board, player):
    for i in range(3):
        if all(board[i][j] == player for j in range(3)): return True
        if all(board[j][i] == player for j in range(3)): return True
    if all(board[i][i] == player for i in range(3)): return True
    if all(board[i][2 - i] == player for i in range(3)): return True
    return False

def check_draw(board):
    return all(board[i][j] != " " for i in range(3) for j in range(3))

def ai_move(board):
    import random
    available_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == " "]
    return random.choice(available_moves) if available_moves else None