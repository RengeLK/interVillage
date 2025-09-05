################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## app.py - main file         ##
## -renge 2024-2025           ##
################################
from flask import Flask, request
import xmltodict
import asyncio
import websockets
import json
import uuid
import time
import subprocess
import schedule
from threading import Thread
from websockets import WebSocketException
import secret, basic, poll, list, presence, msg  # import all other files
from poll import message_queue

app = Flask(__name__)

# Import secrets here so I don't have to rewrite everything
users = secret.users
ads = secret.ads
terms = secret.terms
wvhook = secret.wvhook
address = secret.address
port = secret.port
www_index = open('index.html', 'r')

# Regular browser visitors
@app.route('/', methods=['GET'])
def root():
    return www_index

# Manually add messages to the queue (pre-backend implement)
@app.route('/add', methods=['POST'])
def post():
    data = request.json
    recipient = data['recipient']
    sender = data['sender']
    message_id = data['id']
    content = data['content']
    poll.send_message_to_queue(recipient, sender, message_id, content)
    return "ok"

# Actual IMPS route
# noinspection PyBroadException
@app.route('/imps', methods=['GET', 'POST'])
def imps():
    # Convert XML body to dict
    try:
        imps_data = xmltodict.parse(request.data)
        print("Received IMPS request: ", request.data)
    except:
        resp = form_wv_message({'Status': form_status(503, 'Unknown request type')}, 0)
        return xml_response(resp)

    # Check for specific request types
    if 'WV-CSP-Message' in imps_data:
        return handle_wv_csp_message(imps_data['WV-CSP-Message'])
    resp = form_wv_message({'Status': form_status(501)}, 0)
    return xml_response(resp)

def handle_wv_csp_message(message_request):
    session = message_request.get('Session', {})
    transaction = session.get('Transaction', {})
    transaction_content = transaction.get('TransactionContent', {})

    # Handle Login-Request
    if 'Login-Request' in transaction_content:
        return basic.handle_login(transaction_content['Login-Request'], transaction)

    # Handle Logout-Request
    elif 'Logout-Request' in transaction_content:
        return basic.handle_logout(transaction, session)

    # Handle ClientCapability-Request
    elif 'ClientCapability-Request' in transaction_content:
        return basic.handle_client_capability(transaction_content['ClientCapability-Request'], transaction, session)

    # Handle Service-Request
    elif 'Service-Request' in transaction_content:
        return basic.handle_service_request(transaction_content['Service-Request'], transaction, session)

    # Handle GetList-Request
    elif 'GetList-Request' in transaction_content:
        return list.handle_get_list_request(transaction, session)

    # Handle ListManage-Request
    elif 'ListManage-Request' in transaction_content:
        return list.handle_list_manage_request(transaction_content['ListManage-Request'], transaction, session)

    # Handle BlockEntity-Request
    elif 'BlockEntity-Request' in transaction_content:
        return list.handle_block_request(transaction_content['BlockEntity-Request'], transaction, session)

    #TODO: GetBlockedList-Request

    # Handle UpdatePresence-Request
    elif 'UpdatePresence-Request' in transaction_content:
        return presence.handle_update_presence_request(transaction_content['UpdatePresence-Request'], transaction, session)

    # Handle GetPresence-Request
    elif 'GetPresence-Request' in transaction_content:
        return presence.handle_get_presence_request(transaction_content['GetPresence-Request'], transaction, session)

    # TODO: (Un)SubscribePresence-Request

    # Handle SendMessage-Request
    elif 'SendMessage-Request' in transaction_content:
        return msg.handle_send_message(transaction_content['SendMessage-Request'], transaction, session)

    # Handle KeepAlive-Request
    elif 'KeepAlive-Request' in transaction_content:
        return poll.handle_keep_alive_request(transaction_content['KeepAlive-Request'], transaction, session)

    # Handle Polling-Request
    elif 'Polling-Request' in transaction_content:
        return poll.handle_polling_request(session)

    # Handle MessageDelivered (just ignore it)
    elif 'MessageDelivered' in transaction_content:
        return ''

    # Unknown request type
    else:
        print('!!!!!!!!!!!!! NOT IMPLEMENTED !!!!!!!!!!!!')
        resp = form_wv_message({'Status': form_status(501)}, transaction['TransactionDescriptor']['TransactionID'])
        return xml_response(resp)


def form_status(code: int, desc = None):
    # Almost all the status codes from the specs, right here!
    codes = {
        200: 'Success',
        201: 'Partially Successful',
        202: 'Accepted',

        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Bad Parameter',
        403: 'Forbidden/Bad Login',
        404: 'Not Found',
        405: 'Service Not Supported',
        409: 'Invalid Password',
        415: 'Unsupported Media Type',
        420: 'Invalid Transaction',
        422: 'ClientID Mismatch',
        423: 'Invalid InvitationID',
        426: 'Invalid MessageID',
        431: 'Unauthorized Group',

        500: 'Server Error',
        501: 'Not Implemented',
        503: 'Service Unavailable',
        504: 'Timeout',
        506: 'Service Not Agreed',
        516: 'Domain Forwarding Not Supported',
        531: 'Unknown User',
        532: 'Recipient Blocked Sender',
        536: 'Too Many Hits',
        538: 'Message Rejected',  # by recipient
        540: 'Header Encoding Not Supported',

        600: 'Session Expired',
        601: 'Forced Logout',  # by server
        604: 'Invalid Session',  # doesn't exist
        605: 'New Value Not Accepted',  # KeepAlive

        700: 'Nonexistent Contact List',
        701: 'Contact List Already Exists',
        702: 'Invalid User Properties',
        750: 'Invalid Presence Attribute',
        751: 'Invalid Presence Value'
    }

    if not desc:
        desc = codes[code]
    resp = {
        'Code': code,
        'Description': desc
    }
    return resp


def form_wv_message(content: dict, transaction_id, session_id = None, poll = False):
    # Autodetect server need for polling
    if session_id:
        usid = None
        for n, i in users.items():
            if i['session_id'] == session_id:
                usid = n
        if usid:
            for i in message_queue:
                if i['recipient'] == usid: poll = True

    # If a session ID was provided, make sure to set type to Inband
    # Also finalize the autodetection
    if session_id:
        ses = {
            'SessionType': 'Inband',
            'SessionID': session_id
        }
    else: ses = { 'SessionType': 'Outband' }
    if poll: tr = 'T'
    else: tr = 'F'

    response = {
        'WV-CSP-Message': {
            'Session': {
                'SessionDescriptor': ses,
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction_id,
                        'Poll': tr
                    },
                    'TransactionContent': content
                }
            }
        }
    }
    return response

def gen_msg_id():
    # it is for the repetitive that the simple is IDK
    return 'rm-' + str(uuid.uuid4())

# Convert dict back to XML
def xml_response(data_dict):
    xml_data = xmltodict.unparse(data_dict, pretty=True, full_document=True)
    # Manually add the xmlns
    xml_data = xml_data.replace('<WV-CSP-Message>', '<WV-CSP-Message xmlns="http://www.wireless-village.org/CSP1.1">')
    xml_data = xml_data.replace('<TransactionContent>', '<TransactionContent xmlns="http://www.wireless-village.org/TRC1.1">')
    xml_data = xml_data.replace('<PresenceSubList>', '<PresenceSubList xmlns="http://www.wireless-village.org/PA1.1">')
    return xml_data, 200, {'Content-Type': 'application/xml'}

#####################################
# Here starts Discord WS territory! #
#####################################
GATEWAY_URL = "wss://gateway.discord.gg/?v=9&encoding=json"
last = {}
# WebSocket handler for each user
async def discord_websocket(user_token, user_id):
    async with websockets.connect(GATEWAY_URL, max_size=2 ** 23) as websocket:  # Increased buffer size
        print(f"WebSocket connection established for {user_id}")
        # Step 1: Wait for HELLO (op 10), then authenticate
        await wait_for_hello(websocket, user_token, user_id)
        # Step 2: Handle incoming events
        await handle_events(websocket, user_token, user_id)

# Wait for the HELLO (op 10) event, then send identify
async def wait_for_hello(websocket, token, user_id):
    while True:
        response = await websocket.recv()
        event = json.loads(response)
        if event.get('op') == 10:  # HELLO event
            heartbeat_interval = event['d']['heartbeat_interval'] / 1000
            await identify_with_gateway(websocket, token)
            asyncio.create_task(heartbeat(websocket, heartbeat_interval, token, user_id))
            break

async def handle_events(websocket, token, user_id):
    while True:
        try:
            response = await websocket.recv()
            event = json.loads(response)
        except WebSocketException:
            print(f"Something went wrong when checking WS for {user_id}, attempting to reconnect..")
            await discord_websocket(token, user_id)
            break

        if 's' in event:
            last[token] = event['s']  # Update last known sequence

        if event.get('t') == 'READY':
            print(f"{user_id}'s WebSocket is ready!")

        # TODO: buggy, always responds thrice with only the third one working as expected
        elif event.get('t') == 'MESSAGE_CREATE':  # NewMessage event
            message = event['d']
            author_id = message['author']['id']  # Discord ID of the sender
            author = message['author']['username']  # For printing/logging
            content = message['content']
            message_id = gen_msg_id()

            for user_id2, user_data in users.items():

                # Check if the event author_id matches the 'discord' attribute (meaning they are the sender)
                if 'discord' in user_data and user_data['discord'] == author_id:
                    sender = user_id2  # This user is the sender
                    print(f"New DM for {user_id} from {author}!")
                    poll.send_message_to_queue(user_id, sender, message_id, content)  # Queue the message
                    break

# Send the identify payload to authenticate the WebSocket connection
async def identify_with_gateway(websocket, token):
    identify_payload = {
        "op": 2,  # Opcode for identify
        "d": {
            "token": token,
            "properties": {
                "$os": "Linux",
                "$browser": "Discord Client",
                "$device": "desktop"
            },
            "intents": 4096 | 32768  # DIRECT_MESSAGES + MESSAGE_CONTENT intents
        }
    }
    await websocket.send(json.dumps(identify_payload))

# Send regular heartbeats to keep the WebSocket connection alive
async def heartbeat(websocket, interval, token, user_id):
    while True:
        await asyncio.sleep(interval)
        heartbeat_payload = {"op": 1, "d": last.get(token)}
        try:
            await websocket.send(json.dumps(heartbeat_payload))
        except websockets.ConnectionClosed:
            print("Connection closed during heartbeat! Attempting to reconnect..")
            await discord_websocket(token, user_id)
            break

# Run WebSocket listeners for all users with token
async def run_websockets_for_all_users():
    tasks = [discord_websocket(user_data['token'], user_id) for user_id, user_data in users.items() if 'token' in user_data]
    await asyncio.gather(*tasks)

def run_websockets_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_websockets_for_all_users())
    loop.close()

###########################
# Signal stuff, simpler.. #
###########################
def receive_signal_messages(user_data, user_id):
    phone = user_data['phone']

    subprocess.run(['./signal', '-o', 'json', '-a', phone, 'receive', '--ignore-attachments', '--ignore-stories'])  # initial check, purges messages before server start
    time.sleep(10) # wait a while
    print(f"{user_id}'s Signal receiver is ready!")

    while True:
        try:
            result = subprocess.run(
                ['./signal', '-o', 'json', '-a', phone, 'receive', '--ignore-attachments', '--ignore-stories', "-t", '2', '--max-messages', '1'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Error running signal-cli for {user_id}: {result.stderr}")
                continue

            messages = result.stdout.strip().splitlines()  # Each line is a separate JSON object
            for message_json in messages:
                try:
                    message_data = json.loads(message_json)
                    envelope = message_data.get('envelope', {})
                    sent_message = envelope.get('dataMessage', {})

                    # syncMessage is useless in our case and simply spams the console
                    if 'syncMessage' in envelope:
                        break

                    # Random empty JSONs (probably confirmation?)
                    if not sent_message:
                        break

                    # Extract necessary fields
                    source = envelope.get('sourceNumber')
                    dest = message_data.get('account')
                    content = sent_message.get('message')
                    message_id = gen_msg_id()

                    # Look up the sender in the users dict
                    sender_id = None
                    for user2_id, user_data in users.items():
                        if 'signal' in user_data and user_data['signal'] == source:
                            sender_id = user2_id
                            break

                    if sender_id:
                        print(f"Received Signal message from {sender_id} to {user_id}")
                        poll.send_message_to_queue(user_id, sender_id, message_id, content)

                except json.JSONDecodeError:
                    print(f"Failed to parse message: {message_json}")

        except Exception as e:
            print(f"Error receiving Signal messages for {user_id}: {e}")

        time.sleep(2)

# Thread function for Signal messages
def run_signal_receivers():
    time.sleep(1)  # neat console
    for user_id, user_data in users.items():
        if 'phone' in user_data:
            print(f"Starting Signal receiver for {user_id}")
            Thread(target=receive_signal_messages, args=(user_data,user_id), daemon=True).start()

##############################
# Instagram stuff, similar.. #
# DISCARDED, LEAVING HERE FN #
##############################
"""def receive_instagram(user_data, user_id):
    username = user_data['iguser']
    password = user_data['igpass']

    print(f"IG {user_id}: Logging in..")
    # WARNING: this loads any session, and could log in the wrong user in an actual multi-user installation.
    # Add auto_load_session=False to disable this.
    user_data['instagram'] = Instagram()
    session = user_data['instagram']

    if not session.is_authenticated():
        try:
            print(f"IG {user_id}: No session, logging in manually..")
            session.login(username, password)
        except Exception as e:
            print(f"IG {user_id}: Auth failed!! {e}")

    print(f"IG {user_id}: Logged in as {session.get_account_info()['username']}!!")
    print(f"IG {user_id}: Getting initial messages..")
    print(session.get_messages(limit = 999))
    print(f"{user_id}'s Instagram receiver is ready!")

    while True:
        msgs = session.get_messages()
        print(msgs)
        for msg in msgs:
            source = msg["username"]
            content = msg["text"]
            msgid = gen_msg_id()

            sender_id = None
            for user2_id, user_data in users.items():
                if 'instauser' in user_data and user_data['instauser'] == source:
                    sender_id = user2_id
                    break
            if sender_id:
                print(f"Received Instagram message from {sender_id} to {user_id}")
                poll.send_message_to_queue(user_id, sender_id, msgid, content)
        time.sleep(5)

def run_instagram_receivers():
    time.sleep(1)  # neat console
    for user_id, user_data in users.items():
        if 'iguser' in user_data:
            print(f"Starting Instagram receiver for {user_id}")
            Thread(target=receive_instagram, args=(user_data,user_id), daemon=True).start()"""

# Scheduler thread function
def run_scheduler():
    # Schedule your function
    schedule.every(30).minutes.do(msg.send_advertisements)
    print("Schedule was set!")

    while True:
        schedule.run_pending()  # Run any pending jobs
        time.sleep(1)  # Sleep to avoid high CPU usage


if __name__ == '__main__':
    # Start Flask server in the main thread
    flask_thread = Thread(target=app.run, kwargs={'debug': True, 'use_reloader': False, 'host': '::', 'port': port})
    flask_thread.start()

    # Start WebSocket listeners in a background thread with its own event loop
    ws_thread = Thread(target=run_websockets_thread)
    ws_thread.start()

    # Start Signal polling loop
    signal_thread = Thread(target=run_signal_receivers)
    signal_thread.start()

    # Start the scheduler in a separate thread
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.start()

    # Wait for both threads
    flask_thread.join()
    ws_thread.join()
    signal_thread.join()
    scheduler_thread.join()