# main.py

import telebot
import random
from game import tictactoe as ttt
from game import twentyone as to
from game.twentyone import twentyone_rules

bot = telebot.TeleBot('YOUR-BOT-TOKEN')  # Replace with your bot token

games = {"Tic Tac Toe": {"code": "tictactoe", "players": 2},
         "21 (Blackjack)": {"code": "twentyone", "players": 4}}

rooms = {}
online_users = set()


def close_room(room_code):
    if room_code in rooms:
        for player_id in rooms[room_code]["players"]:
            try:
                bot.send_message(player_id, "The room creator has left. The room is now closed. Returning you to the main menu.")
                back_to_start()
                # update_start_message(message=None, edit=False, user_id=player_id)
            except Exception as e:
                print(f"Error sending message to player {player_id}: {e}")
        del rooms[room_code]


@bot.callback_query_handler(func=lambda call: call.data == "start")
def back_to_start(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id  # Get the chat ID

    for room_code, room_data in list(rooms.items()):
        if user_id in room_data["players"]:
            if user_id == room_data["players"][0]:
                close_room(room_code)
            else:
                rooms[room_code]["players"].remove(user_id)
            break  # Exit the loop after removing the player

    try:
        # Clear chat history (requires appropriate bot permissions)
        bot.delete_message(chat_id, call.message.message_id) # Delete current message first

        if 'message_ids' in rooms[room_code]:
            for message_id in rooms[room_code]['message_ids'].values():
                try:
                    bot.delete_message(user_id, message_id)
                except telebot.apihelper.ApiException as e:
                    print(f"Error deleting message: {e}")

        del rooms[room_code]['message_ids'] #Delete dictionary
            

    except Exception as e:
        print(f"Error clearing chat history or deleting message_ids: {e}")

    update_start_message(message=None, edit=False, user_id=user_id) # Send a new start message


def update_start_message(message=None, edit=False, user_id=None):
    game_info = "\n".join([f"{name} ({details['players']} players)" for name, details in games.items()])
    online_count = len(online_users)
    text = f"Welcome to Mini Games Bot!\nAvailable Games:\n{game_info}\n\nOnline Users: {online_count}\n\nCommands:\n/start - Show this menu\n/newgame - Create a new game\n/join <code> - Join a game"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Create Game", callback_data="create_game"),
               types.InlineKeyboardButton("Join Game", callback_data="join_game"))

    if edit and message:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id, text=text, reply_markup=markup)
    elif user_id:
        bot.send_message(user_id, text, reply_markup=markup)
    elif message:
        bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_command(message):
    online_users.add(message.from_user.id)
    update_start_message(message)


@bot.callback_query_handler(func=lambda call: call.data == "create_game")
def create_game_callback(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for game_name in games:
        markup.add(types.InlineKeyboardButton(game_name, callback_data=f"game_choice:{game_name}"))
    markup.add(types.InlineKeyboardButton("Back", callback_data="start"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Room created! Please choose a game:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("show_players:"))
def show_players_callback(call):
    room_code = call.data.split(":")[1]
    if room_code in rooms:
        player_list = ""
        for player_id in rooms[room_code]["players"]:
            try:
                user = bot.get_chat(player_id)
                username = user.username or user.first_name  # Use username or first name
                player_list += f"- {username}\n"  # Add each player to the list
            except telebot.apihelper.ApiException as e:
                print(f"Error getting user information: {e}")
                player_list += f"- User {player_id}\n" #If the bot cannot access the user's information


        bot.answer_callback_query(call.id, text=f"Players in room {room_code}:\n{player_list}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, text="Room not found!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("game_choice:"))
def game_choice_callback(call):
    game_name = call.data.split(":")[1]
    room_code = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
    rooms[room_code] = {"game": games[game_name]["code"], "players": [call.from_user.id],
                       "current_player": 0, "vs_bot": False}

    if game_name == "21 (Blackjack)":
        rooms[room_code]["deck"] = to.create_deck()
        rooms[room_code]["player_hands"] = {player_id: [] for player_id in rooms[room_code]["players"]}
        rooms[room_code]["dealer_hand"] = []

        markup = types.InlineKeyboardMarkup(row_width=1)
        show_players_button = types.InlineKeyboardButton(f"Players: {len(rooms[room_code]['players'])}/{games[game_name]['players']}", callback_data=f"show_players:{room_code}")
        start_game_button = types.InlineKeyboardButton("Start Game", callback_data=f"start_game:{room_code}")

        markup.add(show_players_button, start_game_button)
        markup.add(telebot.types.InlineKeyboardButton("Back to Menu", callback_data="start"))

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"New {game_name} game created!\nRoom code: {room_code}\n{twentyone_rules}", reply_markup=markup)

    elif game_name == "Tic Tac Toe":
        rooms[room_code]["board"] = ttt.create_board()
        markup = types.InlineKeyboardMarkup()
        copy_button = types.InlineKeyboardButton(text=f"Copy Room Code: {room_code}", callback_data=f"copy:{room_code}", clipboard_data=room_code)
        ai_button = types.InlineKeyboardButton("Play vs AI", callback_data=f"vs_bot:{room_code}")
        markup.row(copy_button)
        markup.row(ai_button)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"New {game_name} game created!\nRoom code: {room_code}", reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data.startswith("hit:"))
def hit_callback(call):
    _, room_code, player_id = call.data.split(":")
    player_id = int(player_id)

    if room_code in rooms and player_id in rooms[room_code]['players'] and rooms[room_code].get("game_started", False): # check for game started
        deck = rooms[room_code]["deck"]
        player_hands = rooms[room_code]["player_hands"]
        message_id = rooms[room_code]['message_ids'][player_id] # Retrieve message_id


        card = to.deal_card(deck)
        player_hands[player_id].append(card)


        show_player_hand(player_id, room_code, message_id)  # Pass message_id to update



def show_player_hand(player_id, room_code, message_id=None):
    player_hands = rooms[room_code]["player_hands"]
    hand_str = to.format_hand(player_hands[player_id])
    hand_value = to.calculate_hand_value([card['rank'] for card in player_hands[player_id]])
    message_text = f"Your hand: {hand_str}\nHand value: {hand_value}"

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    if hand_value > 21:
        message_text = f"Your hand: {hand_str}\nHand value: {hand_value}\nYou busted!"
        markup.add(telebot.types.InlineKeyboardButton("Back to Menu", callback_data="start"))
    elif hand_value <= 21:
        markup.add(telebot.types.InlineKeyboardButton("Hit", callback_data=f"hit:{room_code}:{player_id}"),
                   telebot.types.InlineKeyboardButton("Stand", callback_data=f"stand:{room_code}:{player_id}"))

    # Check if message_ids exists and handle the case where it might not
    if 'message_ids' in rooms[room_code] and player_id in rooms[room_code]['message_ids']:
        try:
            bot.edit_message_text(chat_id=player_id, message_id=rooms[room_code]['message_ids'][player_id],
                                  text=message_text, reply_markup=markup)
        except telebot.apihelper.ApiException as e:
            print(f"Error editing message: {e}")
            sent_message = bot.send_message(player_id, message_text, reply_markup=markup)
            rooms[room_code]['message_ids'][player_id] = sent_message.message_id
    else:  # Send a new message if it can't edit it
        sent_message = bot.send_message(player_id, message_text, reply_markup=markup)
        if 'message_ids' not in rooms[room_code]:
            rooms[room_code]['message_ids'] = {}
        rooms[room_code]['message_ids'][player_id] = sent_message.message_id



@bot.callback_query_handler(func=lambda call: call.data.startswith("start_game:"))
def start_game_callback(call):
    room_code = call.data.split(":")[1]
    if room_code in rooms and call.from_user.id == rooms[room_code]["players"][0]:
        game_name = list(games.keys())[list(games.values()).index({"code": rooms[room_code]["game"], "players": 4})]
        deck = rooms[room_code]["deck"]
        player_hands = rooms[room_code]["player_hands"]
        dealer_hand = rooms[room_code]["dealer_hand"]

        rooms[room_code]['message_ids'] = {}  # Initialize before using it

        for player_id in rooms[room_code]['players']:
            for _ in range(2):
                card = to.deal_card(deck)
                player_hands[player_id].append(card)
            show_player_hand(player_id, room_code)  # Show hands with game controls

        # Dealer's initial hand (one card hidden)
        dealer_hand.append(to.deal_card(deck))
        dealer_hand.append(to.deal_card(deck))
        dealer_hand_str = f"{to.format_hand([dealer_hand[0]])} ?"  # Show first card only
        bot.send_message(call.message.chat.id, f"Dealer's hand: {dealer_hand_str}")

        rooms[room_code]["game_started"] = True  # Mark the game as started
        bot.send_message(call.message.chat.id, "Game started!")

@bot.callback_query_handler(func=lambda call: call.data == "join_game")
def join_game_callback(call):
    available_rooms = []
    for room_code, room_data in rooms.items():
        game_code = room_data["game"]
        game_name = next((name for name, details in games.items() if details["code"] == game_code), None)  # Get game name from game code

        if not game_name:  # Handle the case where game_code is not found in games
            print(f"Warning: Game code '{game_code}' not found in 'games' dictionary.")
            continue  # Skip this room if the game code is invalid

        max_players = games[game_name]["players"]
        if len(room_data["players"]) < max_players:
            available_rooms.append(room_code)

    if available_rooms:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for room_code in available_rooms:
            creator_id = rooms[room_code]['players'][0]
            try:
                creator_username = bot.get_chat_member(call.message.chat.id, creator_id).user.username
            except Exception as e:
                print(f"Error getting username: {e}")
                creator_username = f"User {creator_id}"

            markup.add(types.InlineKeyboardButton(f"Join {creator_username}'s room ({room_code})",
                                                callback_data=f"join_room:{room_code}"))
        markup.add(types.InlineKeyboardButton("Back", callback_data="start"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Choose a room to join:", reply_markup=markup)

    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Back", callback_data="start"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="There are no available rooms to join.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("join_room:"))
def join_room_callback(call):
    room_code = call.data.split(":")[1]
    if room_code not in rooms:
        bot.answer_callback_query(call.id, "This room does not exist!")
        return

    game_code = rooms[room_code]["game"]
    game_name = next((name for name, details in games.items() if details["code"] == game_code), None)

    if not game_name:  # Handle the case where game_code is not found in games
        print(f"Warning: Game code '{game_code}' not found in 'games' dictionary.")
        bot.answer_callback_query(call.id, "Invalid game in this room.")
        return

    max_players = games[game_name]["players"]
    if len(rooms[room_code]["players"]) < max_players and not rooms[room_code].get("game_started", False):  # Check game started
        if call.from_user.id not in rooms[room_code]["players"]:
            rooms[room_code]["players"].append(call.from_user.id)
            bot.answer_callback_query(call.id, f"You joined room {room_code}")

            if "board" in rooms[room_code]:  # Check for tic-tac-toe
                board = rooms[room_code]["board"]
                markup = ttt.format_board(board, room_code)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f"You joined room {room_code}. Game started! Make your move:",
                                      reply_markup=markup)

            elif "deck" in rooms[room_code]:  # Check for twenty-one
                rooms[room_code]["player_hands"][call.from_user.id] = []  # Initialize hand for new player
                markup = types.InlineKeyboardMarkup(row_width=1)
                show_players_button = types.InlineKeyboardButton(
                    f"Players: {len(rooms[room_code]['players'])}/{games[game_name]['players']}",
                    callback_data=f"show_players:{room_code}")

                # Only show the Start Game button to the room creator
                if call.from_user.id == rooms[room_code]['players'][0]:
                    start_game_button = types.InlineKeyboardButton("Start Game",
                                                                callback_data=f"start_game:{room_code}")
                    markup.add(show_players_button, start_game_button)
                else:
                    markup.add(show_players_button)  # Just the "Show Players" button for others

                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f"You joined room {room_code}. Waiting for the game to start.\n{twentyone_rules}",
                                      reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "You are already in this room!")
    elif rooms[room_code].get("game_started", False):
        bot.answer_callback_query(call.id, "This game has already started!")  # Inform if game started
    else:
        bot.answer_callback_query(call.id, "This room is full!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy:"))
def copy_room_code(call):
    room_code = call.data.split(":")[1]
    bot.answer_callback_query(call.id, text=f"Room code {room_code} copied!", show_alert=True)



@bot.callback_query_handler(func=lambda call: call.data.startswith("vs_bot:"))
def vs_bot_callback(call):
    room_code = call.data.split(":")[1]
    if room_code in rooms:
        rooms[room_code]["vs_bot"] = True
        board = rooms[room_code]["board"]
        markup = ttt.format_board(board, room_code) # Use ttt.format_board
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="You started the game vs the bot! Make your move (X):", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("rematch:"))
def rematch_callback(call):
    room_code = call.data.split(":")[1]
    if room_code in rooms:
        rooms[room_code]["board"] = ttt.create_board() # Use ttt.create_board
        rooms[room_code]["current_player"] = 0
        markup = ttt.format_board(rooms[room_code]["board"], room_code) # Use ttt.format_board
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Rematch started! Make your move:", reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "Room not found or game is over.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("move:"))
def handle_move(call):
    _, room_code, row_index, col_index = call.data.split(":")
    room_code, row_index, col_index = room_code, int(row_index), int(col_index)

    if room_code in rooms:
        room = rooms[room_code]
        board = room["board"]

        if call.from_user.id not in room["players"]:
            bot.answer_callback_query(call.id, "You are not in this game!", show_alert=True)
            return

        if board[row_index][col_index] == " ":
            player_symbol = "X" if room["current_player"] == 0 else "O"
            board[row_index][col_index] = player_symbol
            markup = ttt.format_board(board, room_code)  # Use ttt.format_board
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

            if ttt.check_win(board, player_symbol):   # Use ttt.check_win
                game_over(call.message, room_code, f"Player {player_symbol} wins!")
                return

            elif ttt.check_draw(board):  # Use ttt.check_draw
                game_over(call.message, room_code, "It's a draw!")
                return

            room["current_player"] = 1 - room["current_player"]

            if room["vs_bot"] and room["current_player"] == 1:
                ai_move = ttt.ai_move(board)  # Use ttt.ai_move
                if ai_move:
                    board[ai_move[0]][ai_move[1]] = "O"
                    markup = ttt.format_board(board, room_code) # Use ttt.format_board
                    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
                    if ttt.check_win(board, "O"):  # Use ttt.check_win
                        game_over(call.message, room_code, "Bot wins!")  # Use game_over function
                        return
                    elif ttt.check_draw(board):  # Use ttt.check_draw
                         game_over(call.message, room_code, "It's a draw!") # Use game_over function
                         return

                    room["current_player"] = 0



def game_over(message, room_code, result):
    from telebot import types
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("Rematch", callback_data=f"rematch:{room_code}"),
               types.InlineKeyboardButton("Back to Menu", callback_data="start"))
    bot.send_message(message.chat.id, result, reply_markup=markup)



from telebot import types  # Import types here, at the top level of main.py

bot.polling()