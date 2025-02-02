TOKEN = "TOKEN"

import random
import telebot
import threading
import mysql.connector
from telebot import types

bot = telebot.TeleBot(TOKEN)
db_connection = mysql.connector.connect(
    host="localhost",
    user="username",
    password="password",
    database="database_name"
)

db_cursor = db_connection.cursor()

db_cursor.execute("""
CREATE TABLE IF NOT EXISTS game_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_no INT NOT NULL,
    winner VARCHAR(255) NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score INT NOT NULL
)
""")

game_data = {}

# Function to insert game result into database
def insert_game_result(game_no, winner, score):
    sql = "INSERT INTO game_results (game_no, winner, score) VALUES (%s, %s, %s)"
    db_cursor.execute(sql, (game_no, winner, score))
    db_connection.commit()

# Handler for /start command
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(message.chat.id, "Welcome to Rock-Paper-Scissors!\nHow many games would you like to play? "
                                          "Please enter a number.")
        bot.register_next_step_handler(message, ask_num_games)
    except Exception as e:
        print(f"An error occurred in start message handler: {e}")

# Function to handle asking the number of games
def ask_num_games(message):
    try:
        if message.text.isdigit():
            num_games = int(message.text)
            if num_games > 0:
                game_data[message.chat.id] = {'num_games': num_games, 'current_game': 1}
                bot.send_message(message.chat.id, "Let's start playing!")
                play_game(message.chat.id)
            else:
                bot.send_message(message.chat.id, "Please enter a positive number.")
        else:
            bot.send_message(message.chat.id, "Please enter a valid number.")
    except Exception as e:
        print(f"An error occurred in ask_num_games function: {e}")

# Function to play the game
def play_game(chat_id):
    try:
        if chat_id in game_data:
            num_games = game_data[chat_id]['num_games']
            current_game = game_data[chat_id]['current_game']
            if current_game <= num_games:
                bot.send_message(chat_id, f"Game {current_game}:")
                bot.send_message(chat_id, "Click on one of the buttons to make your choice:",
                                 reply_markup=create_choice_keyboard())
                # Start timer thread for this game
                timer_thread = threading.Timer(5, timeout_game, args=[chat_id])
                timer_thread.start()
                game_data[chat_id]['timer_thread'] = timer_thread
            else:
                bot.send_message(chat_id, "Games finished. Thank you for playing!\nNew game -- /start")
        else:
            bot.send_message(chat_id, "Please start the game first using /start command.")
    except Exception as e:
        print(f"An error occurred in play_game function: {e}")

# Function to handle game timeout
def timeout_game(chat_id):
    try:
        if chat_id in game_data and 'timer_thread' in game_data[chat_id]:
            game_data[chat_id]['timer_thread'] = None
            bot.send_message(chat_id, "Time's up! You didn't make a choice in time. You lose!")
            if game_data[chat_id]['current_game'] <= game_data[chat_id]['num_games']:
                game_data[chat_id]['current_game'] += 1
                play_game(chat_id)
            else:
                bot.send_message(chat_id, "Games finished. Thank you for playing!\nNew game -- /start")
    except Exception as e:
        print(f"An error occurred in timeout_game function: {e}")

# Handler for button press
@bot.callback_query_handler(func=lambda call: True)
def handle_button_press(call):
    try:
        player_choice = call.data
        chat_id = call.message.chat.id
        if chat_id in game_data and 'timer_thread' in game_data[chat_id]:
            game_data[chat_id]['timer_thread'].cancel()
            game_data[chat_id]['timer_thread'] = None
            computer_choice = random.choice(['1', '2', '3'])
            result, score = determine_winner(player_choice, computer_choice)
            response = f"Your choice: {get_choice_text(player_choice)}\nComputer's choice: {get_choice_text(computer_choice)}\n{result}"
            bot.send_message(chat_id, response)
            if game_data[chat_id]['current_game'] <= game_data[chat_id]['num_games']:
                game_data[chat_id]['current_game'] += 1
                play_game(chat_id)
            else:
                bot.send_message(chat_id, "Games finished. Thank you for playing!\nNew game -- /start")
            # Insert game result into database
            insert_game_result(game_data[chat_id]['current_game'] - 1, result, score)
        else:
            bot.send_message(chat_id, "Please start the game first using /start command.")
    except Exception as e:
        print(f"An error occurred in handle_button_press function: {e}")

# Function to create keyboard
def create_choice_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("✊", callback_data="1"),
                 types.InlineKeyboardButton("🖐", callback_data="2"),
                 types.InlineKeyboardButton("✌️", callback_data="3"))
    return keyboard

# Function to determine winner and calculate score
def determine_winner(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "It's a tie!", 3  # Tie score
    elif (player_choice == '1' and computer_choice == '3') or \
         (player_choice == '2' and computer_choice == '1') or \
         (player_choice == '3' and computer_choice == '2'):
        return "You win!", 5  # Win score
    else:
        return "Computer wins!", 5  # Lose score

# Function to get choice text
def get_choice_text(choice):
    if choice == '1':
        return "Rock ✊"
    elif choice == '2':
        return "Paper 🖐"
    elif choice == '3':
        return "Scissors ✌️"

# Handler for /records command
@bot.message_handler(commands=['records'])
def show_records(message):
    try:
        # Fetch records from the database ordered by score in descending order
        db_cursor.execute("SELECT winner, SUM(score) AS overall_score FROM game_results GROUP BY winner ORDER BY overall_score DESC")
        records = db_cursor.fetchall()

        if records:
            response = "Overall Records:\n"
            for record in records:
                winner, overall_score = record
                response += f"{winner}: {overall_score}\n"
            bot.send_message(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "No records found.")
    except Exception as e:
        print(f"An error occurred in show_records function: {e}")


# Polling loop
while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"An error occurred while polling: {e}")

# Close MySQL connection
db_cursor.close()
db_connection.close()
