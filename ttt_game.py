# -*- coding: utf-8 -*-
"""
Copyright 2023 Maen Artimy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import json
import random
import string
import time
import paho.mqtt.client as mqtt


PLAYER_X = "X"
PLAYER_O = "O"
TIE_GAME = "T"
GAME_TOPIC = "tic-tac-toe/games"


class MQTTConnetion:
    """
    A Class representing MQTT communication.
    """

    def __init__(self, broker, port, gid):
        self.MQTT_BROKER = broker
        self.MQTT_PORT = port
        self.game_topic = f"{GAME_TOPIC}/{gid}"
        self.player_id = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=6))
        self.remote_player = None
        self.client = None
        self.receive_move = None

    def connect(self):
        # Create an MQTT client and connect to the broker
        self.client = mqtt.Client(client_id=self.player_id)
        self.client.connect(self.MQTT_BROKER, self.MQTT_PORT)

        # Subscribe to the game topic and start the MQTT loop
        self.client.subscribe(self.game_topic)
        self.client.on_message = self.on_message
        self.client.loop_start()

        # Publish a game-start message to the game topic
        request_payload = {"type": "game-start", "player_id": self.player_id}
        self.client.publish(self.game_topic, json.dumps(
            request_payload), qos=1, retain=True)

    # Define a callback function to handle incoming messages
    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload)
        if payload["player_id"] == self.player_id:
            return
        if payload["type"] == "game-start":
            self.handle_game_start(payload)
        elif payload["type"] == "move":
            self.handle_game_move(payload)

    def handle_game_start(self, payload):
        self.remote_player = payload["player_id"]

    def handle_game_move(self, payload):
        # Handle incoming move from the other player
        self.receive_move(payload['row'], payload['col'], payload['winner'])

    def send_move(self, row, col, winner):
        # Publish move to the game topic
        move_payload = {"type": "move",
                        "player_id": self.player_id, "row": row, "col": col,
                        "winner": winner}
        self.client.publish(self.game_topic, json.dumps(move_payload), qos=1)

    def disconnect(self):
        self.client.publish(self.game_topic, payload=None, qos=1, retain=True)
        self.client.disconnect()
        self.client.loop_stop()

    def connected(self):
        return self.remote_player is not None

    def get_my_symbol(self):
        return PLAYER_X if self.player_id >= self.remote_player else PLAYER_O

    def set_receive_move(self, fn):
        self.receive_move = fn


class TTTGame:
    """
    A class representing a Tic-Tac-Toe game.
    """

    def __init__(self, connection):
        """
        Initializes a new Tic-Tac-Toe game.
        """

        self.connection = connection
        self.board = [['']*3, ['']*3, ['']*3]
        self.active = True
        self.my_symbol = connection.get_my_symbol()
        self.other_symbol = PLAYER_O if self.my_symbol == PLAYER_X else PLAYER_X
        self.my_turn = self.my_symbol == PLAYER_X
        self.connection.set_receive_move(self.receive_move)

    def get_input(self, message):
        while True:
            user_input = input(message)
            if user_input.isdigit():
                user_input = int(user_input)
                if 0 <= user_input <= 2:
                    return user_input
            print("Invalid input. Please enter a number between 0 and 2.")

    def test_winning(self):
        # Check rows
        for row in self.board:
            if all(cell == row[0] for cell in row):
                return row[0]

        # Check columns
        for i in range(3):
            if self.board[0][i] == self.board[1][i] == self.board[2][i]:
                return self.board[0][i]

        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return self.board[0][0]

        if self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return self.board[0][2]

        return None

    def test_tie(self):
        return all(cell != '' for row in self.board for cell in row)

    def is_valid_move(self, x, y):
        return self.board[x][y] == ""

    def print_board(self):
        """
        Displays the current state of the Tic-Tac-Toe board.
        """

        for row in self.board:
            print(','.join(map(lambda i: "_" if i == '' else i, row)))

    def update_board(self, x, y, symbol):
        """
        Update the board content
        """

        self.board[x][y] = symbol

    def make_move(self, row, col):
        """
        Sends player's move.
        """
        self.update_board(row, col, self.my_symbol)
        winner = self.check_result()
        self.connection.send_move(row, col, winner)
        self.my_turn = False
        if winner:
            self.active = False
            self.display_result(winner)
        else:
            print(f"Waiting for {self.other_symbol}'s move...")

    def receive_move(self, row, col, winner):
        """
        Receive player's move.

        """
        self.update_board(row, col, self.other_symbol)
        if winner:
            self.display_result(winner)
            self.active = False
            self.my_turn = False
        else:
            print(f"{self.other_symbol} moved to ({row},{col})")
            self.my_turn = True

    def display_result(self, winner):
        message = "It is a Tie" if winner == TIE_GAME else f"{winner} won"
        print(f"Game Over: {message}!")

    def check_result(self):
        # Return 'X', 'O', 'T', or None
        winner = self.test_winning()
        if winner:
            return winner
        if self.test_tie():
            return TIE_GAME
        return None

    def start(self):
        """
        Starts a game of Tic-Tac-Toe.
        """
        
        print("Starting the game ...")
        print(f"You are '{self.my_symbol}'.")
        while self.active:
            if self.my_turn:
                self.print_board()

                # Prompt user to enter their move
                while True:
                    row = self.get_input("Enter row (0-2): ")
                    col = self.get_input("Enter column (0-2): ")
                    if self.is_valid_move(row, col):
                        break
                    print("Invalid move. Try again")

                self.make_move(row, col)
            else:
                time.sleep(1)
        print("Final board:")
        self.print_board()


if __name__ == "__main__":

    # MQTT broker configuration
    MQTT_BROKER = os.getenv('MQTT_BROKER')
    if MQTT_BROKER is None:
        MQTT_BROKER = "localhost"
    print(f"Broker Address: {MQTT_BROKER}")
    MQTT_PORT = 1883

    # Generate a random game ID
    propose_id = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))

    print(f"Suggested Game ID: {propose_id}")
    game_id = input("Enter Game ID:")

    mqtt_conn = MQTTConnetion(MQTT_BROKER, MQTT_PORT, game_id)
    mqtt_conn.connect()

    while not mqtt_conn.connected():
        time.sleep(1)

    # Starting the game
    game = TTTGame(mqtt_conn)
    game.start()

    mqtt_conn.disconnect()
    time.sleep(1)
