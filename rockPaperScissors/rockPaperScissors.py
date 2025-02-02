
TOKEN = "TOKEN"

import random
import telebot
from telebot import types

bot = telebot.TeleBot(TOKEN)

# Dictionary to store game data
game_data = {}

# Function to handle /start command
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(message.chat.id, "Welcome to Rock-Paper-Scissors!\nHow many games would you like to play?\nPlease enter a number.")
        bot.register_next_step_handler(message, ask_num_games)
    except Exception as e:
        print(f"An error occurred in start message handler: {e}")

# Function to ask the user for the number of games
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

# Function to play the next game
def play_game(chat_id):
    try:
        if chat_id in game_data:
            num_games = game_data[chat_id]['num_games']
            current_game = game_data[chat_id]['current_game']
            if current_game <= num_games:
                bot.send_message(chat_id, f"Game {current_game}:")
                bot.send_message(chat_id, "Click on one of the buttons to make your choice:",
                                 reply_markup=create_choice_keyboard())
            else:
                bot.send_message(chat_id, "Games finished. Thank you for playing!\nNew game --> /start")
        else:
            bot.send_message(chat_id, "Please start the game first using /start command.")
    except Exception as e:
        print(f"An error occurred in play_game function: {e}")

# Function to handle button press
@bot.callback_query_handler(func=lambda call: True)
def handle_button_press(call):
    try:
        player_choice = call.data
        computer_choice = random.choice(['1', '2', '3'])
        result = determine_winner(player_choice, computer_choice)
        response = f"Your choice: {get_choice_text(player_choice)}\nComputer's choice: {get_choice_text(computer_choice)}\n{result}"
        bot.send_message(call.message.chat.id, response)
        # Continue to the next game
        if call.message.chat.id in game_data:
            game_data[call.message.chat.id]['current_game'] += 1
            play_game(call.message.chat.id)
    except Exception as e:
        print(f"An error occurred in handle_button_press function: {e}")

# Function to create inline keyboard with choices
def create_choice_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("✊", callback_data="1"),
                 types.InlineKeyboardButton("🖐", callback_data="2"),
                 types.InlineKeyboardButton("✌️", callback_data="3"))
    return keyboard

# Function to determine the winner
def determine_winner(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "It's a tie!"
    elif (player_choice == '1' and computer_choice == '3') or \
         (player_choice == '2' and computer_choice == '1') or \
         (player_choice == '3' and computer_choice == '2'):
         return "You win!"
    else:
        return "Computer wins!"

# Function to get choice text based on choice number
def get_choice_text(choice):
    if choice == '1':
        return "Rock ✊"
    elif choice == '2':
        return "Paper 🖐"
    elif choice == '3':
        return "Scissors ✌️"

# Start the bot with error handling
while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"An error occurred while polling: {e}")
