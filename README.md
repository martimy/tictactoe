# Tic-Tac-Toe Game

This is a simple implementation of a Tic-Tac-Toe game using MQTT protocol. The game uses a client-server architecture where two players connect to a common broker and communicate with each other.

## Requirements

- Python 3.6 or higher
- MQTT server

Python *paho-mqtt* library (can be installed via pip)

```shell
$ pip install -r requirements.txt
```

## Usage

1. Make sure the MQTT broker is installed and running. You can use a free MQTT broker from this [list](https://mntolia.com/10-free-public-private-mqtt-brokers-for-testing-prototyping/).

2. Run the ttt_game.py script on two different machines:

    ```shell
    $ export MQTT_BROKER=example.com
    $ python3 ttt_game.py
    ```

    on Windows

    ```shell
    C:\path>set MQTT_BROKER=example.com
    C:\path>python ttt_game.py
    ```

3. Enter the Game ID when prompted. Make sure that both players enter the same Game ID.
4. Play the game by entering the row and column of the cell where you want to place your symbol.
