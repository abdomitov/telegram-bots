TOKEN = "TOKEN"

import telebot
import mysql.connector
import re
from telebot import types

# Connect to MySQL database
mydb = mysql.connector.connect(
    host="localhost",
    user="username",
    password="password",
    database="database_name"
)

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Command handlers
@bot.message_handler(commands=['start'])

def send_welcome(message):
    bot.reply_to(message, "Welcome! Choose your level /admin to enter Admin panel or /user to enter Market.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Welcome enter your admin username:")
    bot.register_next_step_handler(message, process_admin_username)

def process_admin_username(message):
    chat_id = message.chat.id
    admin_username = message.text.strip()
    bot.send_message(chat_id, "Enter your password:")
    bot.register_next_step_handler(message, lambda msg: process_admin_password(msg, admin_username))

def process_admin_password(message, admin_username):
    chat_id = message.chat.id
    admin_password = message.text.strip()
    try:
        if check_admin_credentials(admin_username, admin_password):
            bot.send_message(chat_id, "Authentication successful! You're now logged in as admin.")
            show_admin_options(chat_id)
        else:
            bot.send_message(chat_id, "Authentication failed. Invalid username or password.\nNew try to /admin \nor\nBack to User menu /user")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
def show_admin_options(chat_id):
    # Creating an inline keyboard with admin options
    keyboard = types.InlineKeyboardMarkup()
    button_add_product = types.InlineKeyboardButton(text="Add Product", callback_data="add_product")
    button_change_product = types.InlineKeyboardButton(text="Change Product", callback_data="change_product")
    button_delete_product = types.InlineKeyboardButton(text="Delete Product", callback_data="delete_product")
    button_show_sold_info = types.InlineKeyboardButton(text="Show Sold Products Info", callback_data="show_sold_info")
    button_show_basket = types.InlineKeyboardButton(text="Show Product", callback_data="show_basket")
    keyboard.row(button_add_product, button_change_product)
    keyboard.row(button_delete_product, button_show_sold_info)
    keyboard.row(button_show_basket)
    bot.send_message(chat_id, "Please select an option:", reply_markup=keyboard)

def check_admin_credentials(admin_username, admin_password):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM admin WHERE admin_name = %s AND admin_password = %s"
        val = (admin_username, admin_password)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False
@bot.callback_query_handler(func=lambda call: call.data == 'add_product')
def add_product_callback(call):
    chat_id = call.message.chat.id
    bot.send_message(chat_id, "Please enter the name of the product:")
    bot.register_next_step_handler(call.message, process_product_name)
def process_product_name(message):
    chat_id = message.chat.id
    product_name = message.text.strip()
    bot.send_message(chat_id, "Please enter the quantity of the product:")
    bot.register_next_step_handler(message, lambda msg: process_product_quantity(msg, product_name))
def process_product_quantity(message, product_name):
    chat_id = message.chat.id
    try:
        product_quantity = int(message.text.strip())
        bot.send_message(chat_id, "Please enter the price of the product:")
        bot.register_next_step_handler(message, lambda msg: process_product_price(msg, product_name, product_quantity))
    except ValueError:
        bot.send_message(chat_id, "Invalid quantity. Please enter a valid number.")
        process_product_name(message)
def process_product_price(message, product_name, product_quantity):
    chat_id = message.chat.id
    try:
        product_price = float(message.text.strip())
        try:
            # Add the product to the database
            add_product_to_database(product_name, product_quantity, product_price)
            bot.send_message(chat_id, "Product added successfully!")
            show_admin_options(chat_id)
        except Exception as e:
            bot.send_message(chat_id, f"An error occurred while adding the product: {str(e)}")
    except ValueError:
        bot.send_message(chat_id, "Invalid price. Please enter a valid number.")
        process_product_quantity(message, product_name)

def add_product_to_database(product_name, product_quantity, product_price):
    try:
        # Insert the product into the database
        cursor = mydb.cursor()
        sql = "INSERT INTO products (pr_name,pr_quantity, price) VALUES (%s, %s, %s)"
        val = (product_name, product_quantity, product_price)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        raise e
current_product_id = {}
@bot.callback_query_handler(func=lambda call: call.data == 'change_product')
def show_all_products(call):
    chat_id = call.message.chat.id
    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT pr_id, pr_name, pr_quantity, price FROM products")
        products = cursor.fetchall()

        message = "Here are all the products:\n"
        for product in products:
            message += f"ID: {product[0]}\n"
            message += f"Name: {product[1]}\n"
            message += f"Quantity: {product[2]}\n"
            message += f"Price: {product[3]}\n"
            message += "\n"

        bot.send_message(chat_id, message)
        bot.send_message(chat_id, "Enter the ID of the product you want to update:")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def choose_product(message):
    chat_id = message.chat.id
    try:
        product_id = int(message.text.strip())  # Try to convert the message to an integer
        current_product_id[chat_id] = product_id  # Store the selected product ID
        change_product_callback(message)
    except ValueError:
        # If the message is not a valid integer, it's not a product ID
        bot.send_message(chat_id, "Invalid input. Please enter the ID of the product you want to update.")


def change_product_callback(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "What do you want to change for the product? Choose one:",
                     reply_markup=get_change_options_keyboard())
def get_change_options_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton(text="Change Name", callback_data="change_name"),
                 types.InlineKeyboardButton(text="Change Quantity", callback_data="change_quantity"))
    keyboard.row(types.InlineKeyboardButton(text="Change Price", callback_data="change_price"))
    return keyboard
@bot.callback_query_handler(func=lambda call: call.data.startswith('change_'))
def process_change_option(call):
    chat_id = call.message.chat.id
    option = call.data.split('_')[-1]
    if option == 'name':
        bot.send_message(chat_id, "Enter the new name for the product:")
        bot.register_next_step_handler(call.message, lambda msg: process_new_name(msg))
    elif option == 'quantity':
        bot.send_message(chat_id, "Enter the new quantity for the product:")
        bot.register_next_step_handler(call.message, lambda msg: process_new_quantity(msg))
    elif option == 'price':
        bot.send_message(chat_id, "Enter the new price for the product:")
        bot.register_next_step_handler(call.message, lambda msg: process_new_price(msg))

def process_new_name(message):
    chat_id = message.chat.id
    new_name = message.text.strip()
    try:
        cursor = mydb.cursor()
        sql = "UPDATE products SET pr_name = %s WHERE pr_id = %s"  # Update 'product_id' to 'pr_id'
        val = (new_name, current_product_id[chat_id])
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        bot.send_message(chat_id, f"Product name updated to: {new_name}")
        show_admin_options(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def process_new_quantity(message):
    chat_id = message.chat.id
    new_quantity_str = message.text.strip()
    try:
        new_quantity = int(new_quantity_str)
    except ValueError:
        bot.send_message(chat_id, "Quantity must be an integer.")
        return
    try:
        cursor = mydb.cursor()
        sql = "UPDATE products SET pr_quantity = %s WHERE pr_id = %s"  # Replace 'product_id' with 'pr_id'
        val = (new_quantity, current_product_id[chat_id])
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        bot.send_message(chat_id, f"Product quantity updated to: {new_quantity}")
        show_admin_options(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def process_new_price(message):
    chat_id = message.chat.id
    new_price_str = message.text.strip()
    try:
        new_price = float(new_price_str)
    except ValueError:
        bot.send_message(chat_id, "Price must be a float.")
        return
    try:
        cursor = mydb.cursor()
        sql = "UPDATE products SET price = %s WHERE pr_id = %s"  # Use the correct column name here
        val = (new_price, current_product_id[chat_id])
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        bot.send_message(chat_id, f"Product price updated to: {new_price}")
        show_admin_options(chat_id)  # Call the function to display options again
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

# Function to display all products with their IDs
def show_all_products_for_deletion(chat_id):
    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT pr_id, pr_name FROM products")
        products = cursor.fetchall()

        message = "Here are all the products:\n"
        for product in products:
            message += f"ID: {product[0]}\n"
            message += f"Name: {product[1]}\n"

        bot.send_message(chat_id, message)
        bot.send_message(chat_id, "Enter the ID of the product you want to delete:")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

# Function to handle the deletion process
@bot.callback_query_handler(func=lambda call: call.data == 'delete_product')
def delete_product_callback(call):
    chat_id = call.message.chat.id
    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT pr_id, pr_name, pr_quantity, price FROM products")
        products = cursor.fetchall()

        if not products:
            bot.send_message(chat_id, "No products available.")
            return

        message = "Here are all the products:\n"
        for product in products:
            message += f"ID: {product[0]}\n"
            message += f"Name: {product[1]}\n"
            message += f"Quantity: {product[2]}\n"
            message += f"Price: {product[3]}\n"
            message += "\n"

        bot.send_message(chat_id, message)
        bot.send_message(chat_id, "Please enter the ID of the product you want to delete:")
        bot.register_next_step_handler(call.message, process_product_deletion)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def process_product_deletion(message):
    chat_id = message.chat.id
    product_id = message.text.strip()

    try:
        cursor = mydb.cursor()

        sql_delete_basket = "DELETE FROM basket WHERE pr_id = %s"
        cursor.execute(sql_delete_basket, (product_id,))

        sql_delete_product = "DELETE FROM products WHERE pr_id = %s"
        cursor.execute(sql_delete_product, (product_id,))

        mydb.commit()
        cursor.close()
        bot.send_message(chat_id, f"Product with ID {product_id} deleted successfully.")
        show_admin_options(chat_id)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

# Function to handle the callback for showing sold products info
@bot.callback_query_handler(func=lambda call: call.data == 'show_sold_info')
def show_sold_products_info(call):
    chat_id = call.message.chat.id
    try:
        cursor = mydb.cursor()

        # Count the number of sold products
        cursor.execute("SELECT COUNT(*) FROM basket WHERE pr_status = 'True'")
        sold_product_count = cursor.fetchone()[0]

        bot.send_message(chat_id, f"Number of sold products: {sold_product_count}")
    except mysql.connector.Error as e:
        bot.send_message(chat_id, f"An error occurred while fetching sold products count: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"An unexpected error occurred: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'show_basket')
def show_basket(call):
    chat_id = call.message.chat.id
    try:
        cursor = mydb.cursor()

        # Fetch products from the product table
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        if not products:
            bot.send_message(chat_id, "No products available.")
            return

        message = "Products in the basket:\n"
        for product in products:
            message += f"ID: {product[0]}\n"
            message += f"Name: {product[1]}\n"
            message += f"Quantity: {product[2]}\n"
            message += f"Price: {product[3]}\n"
            message += "\n"

        bot.send_message(chat_id, message)
        show_admin_options(chat_id)
    except mysql.connector.Error as e:
        bot.send_message(chat_id, f"An error occurred while fetching products: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"An unexpected error occurred: {e}")




@bot.message_handler(commands=['user'])
def user_panel(message):
    bot.reply_to(message, "Welcome! Use /register to register or /login to login.")

@bot.message_handler(commands=['register'])
def register(message):
    try:
        msg = bot.send_message(message.chat.id, "Enter your username:")
        bot.register_next_step_handler(msg, process_username_step)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def process_username_step(message):
    try:
        username = message.text.strip()
        chat_id = message.chat.id
        if username:
            if chat_id_exists(chat_id):
                bot.reply_to(message, "You already have a username. Please try /login to logging in.")
            elif not username_exists(username):
                bot.username = username
                msg = bot.send_message(chat_id, "Enter your password:")
                bot.register_next_step_handler(msg, process_password_step)
            else:
                bot.send_message(chat_id, "Username already exists. Please choose another username.")
                # Ask for username again
                msg = bot.send_message(chat_id, "Enter your username:")
                bot.register_next_step_handler(msg, process_username_step)
        else:
            bot.send_message(chat_id, "Invalid input. Please try again.")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
def chat_id_exists(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM users WHERE chat_id = %s"
        val = (chat_id,)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def username_exists(username):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM users WHERE username = %s"
        val = (username,)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def process_password_step(message):
    try:
        password = message.text.strip()
        chat_id = message.chat.id
        if is_valid_password(password):
            username = bot.username
            insert_user(chat_id, username, password)
            bot.send_message(chat_id, "Registration successful! Now use /login to login.")
        else:
            bot.send_message(chat_id, "Password must meet the following requirements:\n"
                                       "- Minimum 8 characters\n"
                                       "- At least 1 uppercase letter\n"
                                       "- At least 1 number\n"
                                       "- At least 1 symbol\n"
                                       "Please try again.")
            # Ask for password again
            msg = bot.send_message(chat_id, "Enter your password:")
            bot.register_next_step_handler(msg, process_password_step)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def is_valid_password(password):
    try:
        regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+=\-{}[\]:;\"'|\\<,>.?/])(?=.*[a-z]).{8,}$"
        return bool(re.match(regex, password))
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")
def insert_user(chat_id, username, password):
    try:
        cursor = mydb.cursor()
        sql = "INSERT INTO users (chat_id, username, password) VALUES (%s, %s, %s)"
        val = (chat_id, username, password)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.message_handler(commands=['login'])
def login(message):
    try:
        msg = bot.send_message(message.chat.id, "Enter your username:")
        bot.register_next_step_handler(msg, process_login_username_step)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def process_login_username_step(message):
    try:
        username = message.text.strip()
        chat_id = message.chat.id
        if username:
            bot.username = username
            msg = bot.send_message(chat_id, "Enter your password:")
            bot.register_next_step_handler(msg, process_login_password_step)
        else:
            bot.send_message(chat_id, "Invalid input. Please try again.")
            # Ask for username again
            msg = bot.send_message(chat_id, "Enter your username:")
            bot.register_next_step_handler(msg, process_login_username_step)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def get_products_keyboard():
    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        keyboard = telebot.types.InlineKeyboardMarkup()
        for product in products:
            button = telebot.types.InlineKeyboardButton(text=f"{product[1]} - Price: {product[3]}", callback_data=f"add_to_basket_{product[0]}")
            keyboard.add(button)
        keyboard.row(telebot.types.InlineKeyboardButton("Go to Checkout", callback_data="go_to_checkout"))
        cursor.close()
        return keyboard
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'go_to_checkout')
def go_to_checkout_callback(call):
    try:
        show_basket_callback(call)
        show_products_button = telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(show_products_button)
        bot.send_message(call.message.chat.id, "Choose an action:", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def process_login_password_step(message):
    try:
        password = message.text.strip()
        chat_id = message.chat.id
        username = bot.username
        if check_login(chat_id, username, password):
            # Save chat_id as user_id in bot context
            bot.user_id = chat_id
            bot.send_message(chat_id, "Hello! Here are the available options:")
            # Display options
            options_keyboard = telebot.types.InlineKeyboardMarkup()
            options_keyboard.row(
                telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products"),
                telebot.types.InlineKeyboardButton("Show Basket", callback_data="show_basket"))
            bot.send_message(chat_id, "Choose an option:", reply_markup=options_keyboard)
        else:
            bot.send_message(chat_id, "Login failed. Invalid username or password.")
            # Ask for username again
            msg = bot.send_message(chat_id, "Enter your username:")
            bot.register_next_step_handler(msg, process_login_username_step)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def check_login(chat_id, username, password):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM users WHERE chat_id = %s AND username = %s AND password = %s"
        val = (chat_id, username, password)
        cursor.execute(sql, val)
        result = cursor.fetchone()
        cursor.close()
        return result is not None
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

current_product = {}

# Callback function for adding product to basket
@bot.callback_query_handler(func=lambda call: call.data.startswith('add_to_basket_'))
def add_to_basket_callback(call):
    try:
        chat_id = call.message.chat.id
        product_id = call.data.split('_')[-1]
        product = get_product_by_id(product_id)
        if product:
            current_product[chat_id] = product  # Store the current product for this chat ID
            # Ask the user for the quantity of the current product
            quantity_msg = bot.send_message(chat_id, f"How many kg of {product[1]} would you like to add to your basket?")
            bot.register_next_step_handler(quantity_msg, process_quantity_step)
        else:
            bot.send_message(chat_id, "Product not found.")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def get_product_by_id(product_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM products WHERE pr_id = %s"
        val = (product_id,)
        cursor.execute(sql, val)
        product = cursor.fetchone()
        cursor.close()
        return product
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('process_quantity_step'))
# Define process_quantity_step function
def process_quantity_step(message):
    try:
        chat_id = message.chat.id
        product = current_product.get(chat_id)  # Get the current product for this chat ID
        if product:
            quantity = message.text.strip()
            if quantity.isdigit():
                overall_price = float(quantity) * product[3]
                insert_into_basket(chat_id, product[0], product[1], int(quantity), overall_price)
                bot.send_message(chat_id, f"{quantity} kg of {product[1]} added to your basket.")
                # Ask for product selection again
                keyboard = get_products_keyboard()
                bot.send_message(chat_id, "Choose a product:", reply_markup=keyboard)
            else:
                bot.send_message(chat_id, "Invalid quantity. Please enter a valid number.")
        else:
            bot.send_message(chat_id, "No product selected. Please choose a product first.")
            # Ask for product selection again
            keyboard = get_products_keyboard()
            bot.send_message(chat_id, "Choose a product:", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

# Now use process_quantity_step in the lambda function
@bot.callback_query_handler(func=lambda call: call.data.startswith('process_quantity_step'))
def process_quantity_callback(call):
    try:
        chat_id = call.message.chat.id
        product_id = call.data.split('_')[-1]
        product = get_product_by_id(product_id)
        if product:
            quantity_msg = bot.send_message(chat_id, f"How many kg of {product[1]} would you like to add to your basket?")
            bot.register_next_step_handler(quantity_msg, lambda msg: process_quantity_step(msg, product))
        else:
            bot.send_message(chat_id, "Product not found.")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def insert_into_basket(chat_id, pr_id, pr_name, pr_quantity, overall_price):
    try:
        cursor = mydb.cursor()
        sql = "INSERT INTO basket (user_id, pr_id, pr_name, pr_quantity, overall_price) VALUES (%s, %s, %s, %s, %s)"
        val = (chat_id, pr_id, pr_name, pr_quantity, overall_price)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'show_products')
def show_products_callback(call):
    try:
        chat_id = call.message.chat.id
        keyboard = get_products_keyboard()
        if keyboard:
            bot.send_message(chat_id, "Products:", reply_markup=keyboard)
        else:
            bot.send_message(chat_id, "No products available.")
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'show_basket')
def show_basket_callback(call):
    try:
        chat_id = call.message.chat.id
        basket = get_basket(chat_id)
        if basket:
            basket_text = "\n".join([f"{item[2]} - Quantity: {item[3]}, Overall Price: {item[4]}" for item in basket])
            bot.send_message(chat_id, f"Basket:\n{basket_text}")
            basket_keyboard = telebot.types.InlineKeyboardMarkup()
            basket_keyboard.row(
                telebot.types.InlineKeyboardButton("Confirm Payment", callback_data="confirm_payment"),
                telebot.types.InlineKeyboardButton("Clear Basket", callback_data="clear_basket"),
                telebot.types.InlineKeyboardButton("Show Shopping History", callback_data="show_shopping_history"),
                telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
            )
            bot.send_message(chat_id, "Choose an action:", reply_markup=basket_keyboard)
        else:
            bot.send_message(chat_id, "Your basket is empty.")

    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def get_basket(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM basket WHERE user_id = %s AND pr_status IS NULL"
        val = (chat_id,)
        cursor.execute(sql, val)
        basket = cursor.fetchall()
        cursor.close()
        return basket
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_payment')
def confirm_payment_callback(call):
    try:
        chat_id = call.message.chat.id
        total_price = get_total_price(chat_id)
        if total_price is not None:
            update_basket_status(chat_id, True)
            update_product_quantity(chat_id)  # Call to update product quantities
            bot.send_message(chat_id, f"Payment confirmed. Thank you for your purchase! Total price: ${round(total_price,2)}")
            # Add the "Show Products" and "Show Shopping History" buttons
            show_products_button = telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
            show_history_button = telebot.types.InlineKeyboardButton("Show Shopping History", callback_data="show_shopping_history")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(show_products_button, show_history_button)
            bot.send_message(chat_id, "Choose an action:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Your basket is empty. Please add items before confirming payment.")
            show_products_button = telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(show_products_button)
            bot.send_message(chat_id, "Choose an action:", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def update_product_quantity(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT pr_id, pr_quantity FROM basket WHERE user_id = %s AND pr_status IS NULL"
        val = (chat_id,)
        cursor.execute(sql, val)
        basket_items = cursor.fetchall()
        for item in basket_items:
            pr_id, pr_quantity = item
            update_quantity_sql = "UPDATE products SET pr_quantity = pr_quantity - %s WHERE pr_id = %s"
            update_quantity_val = (pr_quantity, pr_id)
            cursor.execute(update_quantity_sql, update_quantity_val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def get_total_price(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT SUM(overall_price) FROM basket WHERE user_id = %s AND pr_status IS NULL"
        val = (chat_id,)
        cursor.execute(sql, val)
        total_price = cursor.fetchone()[0]
        cursor.close()
        return total_price
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'clear_basket')
def clear_basket_callback(call):
    try:
        chat_id = call.message.chat.id
        clear_basket(chat_id)
        bot.send_message(chat_id, "Basket cleared.")
        # Add the "Show Products" and "Show Shopping History" buttons
        show_products_button = telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
        show_history_button = telebot.types.InlineKeyboardButton("Show Shopping History", callback_data="show_shopping_history")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(show_products_button, show_history_button)
        bot.send_message(chat_id, "Choose an action:", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


def update_basket_status(chat_id, status):
    try:
        cursor = mydb.cursor()
        sql = "UPDATE basket SET pr_status = %s WHERE user_id = %s AND pr_status IS NULL"
        val = ("True" if status else "False", chat_id)  # Convert boolean status to string "True" or "False"
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def clear_basket(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "UPDATE basket SET pr_status = 'False' WHERE user_id = %s AND pr_status IS NULL"
        val = (chat_id,)
        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == 'show_shopping_history')
def show_shopping_history_callback(call):
    try:
        chat_id = call.message.chat.id
        shopping_history = get_shopping_history(chat_id)
        if shopping_history:
            history_text = "\n".join([f"{item[2]} - Quantity: {item[3]}, Overall Price: {item[4]}" for item in shopping_history])
            bot.send_message(chat_id, f"Shopping History:\n{history_text}")
        else:
            bot.send_message(chat_id, "No shopping history.")
        show_products_button = telebot.types.InlineKeyboardButton("Show Products", callback_data="show_products")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(show_products_button)
        bot.send_message(chat_id, "Choose an action:", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")

def get_shopping_history(chat_id):
    try:
        cursor = mydb.cursor()
        sql = "SELECT * FROM basket WHERE user_id = %s AND pr_status = 'True'"
        val = (chat_id,)
        cursor.execute(sql, val)
        shopping_history = cursor.fetchall()
        cursor.close()
        return shopping_history
    except Exception as e:
        bot.send_message(chat_id, f"An error occurred: {str(e)}")


if __name__ == '__main__':
    bot.polling()
