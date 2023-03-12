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
import paho.mqtt.client as mqtt

# MQTT broker configuration
broker_address = os.getenv('MQTT_BROKER')
if broker_address is None:
    broker_address = "localhost"
print(f"Broker Address: {broker_address}")
broker_port = 1883

# Generate a random ID for this player
player_id = ''.join(random.choices(string.digits, k=6))

# Generate a random game ID
propose_id = ''.join(random.choices(
    string.ascii_uppercase + string.digits, k=6))


# Create an MQTT client and connect to the broker
client = mqtt.Client(client_id=player_id)
client.connect(broker_address, broker_port)


def get_input(message):
    while True:
        user_input = input(message)
        if user_input.isdigit():
            user_input = int(user_input)
            if 0 <= user_input <= 2:
                return user_input
        print("Invalid input. Please enter a number between 0 and 2.")


class Game:
    def __init__(self, gid, pid):
        self.game_topic = f"tic-tac-toe/games/{gid}"
        self.player_id = pid
        self.board = [['']*3, ['']*3, ['']*3]
        self.my_turn = False
        self.my_symbol = ""
        self.winner = None
        self.active = True

    def test_wining(self):
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

    def valid_move(self, x, y):
        return self.board[x][y] == ""

    def handle_game_start(self, payload):
        # Determine whether this player is X or O
        if payload["player_id"] > player_id:
            self.my_symbol = "O"
            self.my_turn = False
        else:
            self.my_symbol = "X"
            self.my_turn = True

    def handle_game_move(self, payload):
        # Handle incoming move from the other player
        print(
            f"Received move from player {payload['player_id']}: \
                ({payload['row']}, {payload['col']})")
        if self.valid_move(payload['row'], payload['col']):
            self.board[payload['row']][payload['col']
                                       ] = "O" if self.my_symbol == "X" else "X"
            self.winner = self.test_wining()
            if not self.winner:
                # no winner
                if self.test_tie():
                    payload = {"type": "game-end", "player_id": player_id}
                    client.publish(self.game_topic, json.dumps(payload))
                    self.handle_game_over()
                else:
                    self.my_turn = True
            else:
                payload = {"type": "game-end", "player_id": player_id}
                client.publish(self.game_topic, json.dumps(payload))
                self.handle_game_over()
        else:
            invalid_payload = {"type": "invalid", "player_id": player_id}
            client.publish(self.game_topic, json.dumps(invalid_payload))
            self.my_turn = False

    def handle_game_invalid(self):
        print("Invalid move. Try again")
        self.my_turn = True

    def handle_game_over(self):
        client.disconnect()
        self.active = False

    # Define a callback function to handle incoming messages
    def on_message(self, client, userdata, message):
        payload = json.loads(message.payload)
        if payload["player_id"] == player_id:
            return
        if payload["type"] == "game-start":
            self.handle_game_start(payload)
        elif payload["type"] == "move":
            self.handle_game_move(payload)
        elif payload["type"] == "invalid":
            self.handle_game_invalid()
        elif payload["type"] == "game-end":
            self.handle_game_over()

    def print_board(self):
        for row in self.board:
            print(','.join(map(lambda i: "_" if i == '' else i, row)))

    def update_board(self, x, y):
        self.board[x][y] = self.my_symbol

    def start(self):
        while self.active:
            if self.my_turn:
                # Prompt user to enter their move
                self.print_board()

                row = get_input("Enter row (0-2): ")
                col = get_input("Enter column (0-2): ")

                self.update_board(row, col)

                # Publish move to the game topic
                move_payload = {"type": "move",
                                "player_id": player_id, "row": row, "col": col}
                client.publish(game.game_topic, json.dumps(move_payload))
                self.my_turn = False
            else:
                pass


print(f"Your Player ID: {player_id}, Game ID: {propose_id}")
game_id = input("Enter Game ID:")
game = Game(game_id, player_id)

# Subscribe to the game topic and start the MQTT loop
client.subscribe(game.game_topic)
client.on_message = game.on_message
client.loop_start()


# Publish a game-start message to the game topic
request_payload = {"type": "game-start", "player_id": player_id}
client.publish(game.game_topic, json.dumps(request_payload), retain=True)


game.start()

print("Game Over!")
print(game.print_board())
