import json
import socket
import threading
from queue import Queue

import gym
import numpy as np

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1, 2]
queue = Queue()
all_connections = []
all_address = []

# Create a Socket ( connect two computers)
def create_socket():
    try:
        global host
        global port
        global s

        s = socket.socket()
        host = socket.gethostname()
        port = 9999

    except socket.error as msg:
        print("Socket creation error: " + str(msg))

# Binding the socket and listening for connections
def bind_socket():
    try:
        global host
        global port
        global s
        print("Binding at : ", host, port)

        s.bind((host, port))
        s.listen(5)

    except socket.error as msg:
        print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
        bind_socket()

# THREAD num 1
# Handling connection from multiple clients and saving to a list
# Closing previous connections when server.py file is restarted
def accepting_connections():
    for c in all_connections:
        c.close()

    del all_connections[:]
    del all_address[:]

    while True:
        try:
            conn, address = s.accept()
            s.setblocking(1)  # prevents timeout

            all_connections.append(conn)
            all_address.append(address)

            print("Connection has been established :" + address[0])

        except:
            print("Error accepting connections")
            break

# THREAD num 2
# 1) See all the clients
# 2) Select a client
# 3) Send game options to the client
# 4) Launch game
#    loop:
# 5) Send game info
# 6) get action
# 7) Play action or end game

def game_manager():

    while True:
        cmd = input('manager> ')
        if cmd == 'list':
            list_connections()
        elif cmd == 'quit':
            close_server()
            break
        elif 'select' in cmd:
            try:
                target = cmd.split(' ')[1]
                conn = get_target(target)
                send_games(conn)
                # Deals with client connection commands
                client_selected(conn)

            except:
                conn.send(str.encode('end'))
                print('Problem with target.')
        else:
            print("Command not recognized")


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

# Client commands
def client_selected(conn):
    # Receive game option
    game = conn.recv(1024).decode()
    game = int(game)
    all_envs = gym.envs.registry.all()
    env_ids = [env_spec.id for env_spec in all_envs]
    print('Game slected:', env_ids[game])
    env = gym.make(env_ids[game])
    # send possible spaces
    spaces = [env.observation_space.shape, \
              env.action_space.n]

    pack = json.dumps(dict(enumerate(spaces)), cls=NumpyEncoder)
    conn.send(pack.encode())
    print('Game info sent.')
    play_game(conn, env)


def encode_step(data):
    return json.dumps(dict(enumerate(data)), cls=NumpyEncoder)


# Loop through episodes
def play_game(conn, env):
    print('play game function')
    NUM_EPISODES = 200
    state_0 = env.reset()
    conn.send(encode_step(state_0).encode())
    print('Sent state 0')
    data = env.step(env.action_space.sample())
    pack = encode_step(data)
    conn.send(pack.encode())
    for episode in range(NUM_EPISODES):
        #env.render()
        # get action
        action_n = conn.recv(1024).decode()
        action_n = int(action_n)
        data = env.step(action_n)  # take a random action

        done=data[2]
        if done:
            print('Done hit')
            conn.send(str.encode('end'))
            break
        pack = encode_step(data)
        conn.send(pack.encode())

    conn.send(str.encode('end'))
    env.close()

# Send games
def send_games(conn):
    # send game options
    all_envs = gym.envs.registry.all()
    env_ids = [env_spec.id for env_spec in all_envs]
    pack = json.dumps(dict(enumerate(env_ids[:10])))
    conn.send(pack.encode())

# Display all current active connections with client
def list_connections():
    results = ''
    for i, conn in enumerate(all_connections):
        try:
            conn.send(str.encode('handshake'))
            conn.recv(20480)
        except:
            del all_connections[i]
            del all_address[i]
            continue

        results = str(i) + "   " + str(all_address[i][0]) + "   " + str(all_address[i][1]) + "\n"

    print("----Clients----" + "\n" + results)


# Selecting the target
def get_target(target):
    try:
        target = int(target)
        conn = all_connections[target]
        print("You are now connected to :" + str(all_address[target][0]))
        conn.send(str.encode('selected'))
        return conn

    except:
        print("Selection not valid")
        return None

def close_server():
    global s
    s.close()


# Create worker threads
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()


# Do next job that is in the queue (handle connections, send commands)
def work():
    while True:
        x = queue.get()
        if x == 1:
            create_socket()
            bind_socket()
            accepting_connections()
        if x == 2:
            game_manager()

        queue.task_done()


def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)

    queue.join()

create_workers()
create_jobs()