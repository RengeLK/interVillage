################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## app.py - main file         ##
## -renge 2024                ##
################################
from flask import Flask, request
import xmltodict
import asyncio
import websockets
import json
from threading import Thread
import secret, basic, poll, list, presence, msg  # import all other files

app = Flask(__name__)

# Import secrets here so I don't have to rewrite everything
users = secret.users
terms = secret.terms
wvhook = secret.wvhook

# Regular browser visitors
@app.route('/', methods=['GET'])
def root():
    return 'you need an imps client to connect to intervillage\n-renge 2024'

# Manually add messages to the queue (pre-backend implement)
'''@app.route('/add', methods=['POST'])
def post():
    data = xmltodict.parse(request.data)['xml']
    recipient = data['recipient']
    sender = data['sender']
    message_id = data['id']
    content = data['content']
    poll.send_message_to_queue(recipient, sender, message_id, content)
    return '''

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

    # Handle UpdatePresence-Request
    elif 'UpdatePresence-Request' in transaction_content:
        return presence.handle_update_presence_request(transaction_content['UpdatePresence-Request'], transaction, session)

    # Handle GetPresence-Request
    elif 'GetPresence-Request' in transaction_content:
        return presence.handle_get_presence_request(transaction_content['GetPresence-Request'], transaction, session)

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
        751: 'Invalid Presence Value',
        # Skipping 8xx: Groups
        900: 'Multiple Errors'
    }

    if not desc:
        desc = codes[code]
    resp = {
        'Code': code,
        'Description': desc
    }
    return resp


def form_wv_message(content: dict, transaction_id, session_id = None):
    # If a session ID was provided, make sure to set type to Inband
    if session_id:
        ses = {
            'SessionType': 'Inband',
            'SessionID': session_id
        }
    else: ses = { 'SessionType': 'Outband' }

    response = {
        'WV-CSP-Message': {
            'Session': {
                'SessionDescriptor': ses,
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction_id,
                        'Poll': 'F'
                    },
                    'TransactionContent': content
                }
            }
        }
    }
    return response

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
last = {}  # keeps track of last event for heartbeat

# WebSocket function to handle real-time DMs for a specific user
async def listen_for_dms(user_token, user_id):
    async with websockets.connect(GATEWAY_URL) as websocket:
        await identify_with_gateway(websocket, user_token)

        while True:
            response = await websocket.recv()
            event = json.loads(response)
            last[user_token] = event.get('s')
            if event.get('t') == 'MESSAGE_CREATE':  # NewMessage event
                message = event['d']
                if message['guild_id'] is None:  # DMs only

                    author_id = message['author']['id']  # discord id
                    author = message['author']['username']  # only for print()
                    sender = None
                    message_id = 'dcmsgidk'
                    content = message['content']

                    for userr_id, user_data in users.items():  # find the actual author through 'discord'
                        if 'discord' in user_data and user_data['discord'] == author_id:
                            sender = userr_id
                            print(f"New DM! for {user_id} from {author}: {content}")
                            poll.send_message_to_queue(user_id, sender, message_id, content)  # send it!
                        else:
                            # we don't care about this message since the sender is not in the db
                            print(f"some random message came in from {author}")
                            break


            elif event.get('op') == 10:  # HELLO event with heartbeat information
                heartbeat_interval = event['d']['heartbeat_interval'] / 1000
                # Start the heartbeat loop
                asyncio.create_task(heartbeat(websocket, heartbeat_interval, user_token))

# Identify function to authenticate with the Discord WebSocket Gateway
async def identify_with_gateway(websocket, token):
    payload = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Linux",
                "$browser": "Mozilla Firefox",
                "$device": "Discord Client",
                "$browser_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.71 Chrome/128.0.6613.36 Electron/32.0.0 Safari/537.36"
            },
            "intents": 513  # To listen for DMs (512) and basic events (1)
        }
    }
    await websocket.send(json.dumps(payload))

# Heartbeat function to keep the connection alive
async def heartbeat(websocket, interval, token):
    while True:
        await asyncio.sleep(interval)  # Wait for the heartbeat interval
        heartbeat_payload = {
            "op": 1,
            "d": last[token]  # add the last known event of specific token
        }
        await websocket.send(json.dumps(heartbeat_payload))

# Run WebSocket listeners for all users with a valid Discord token
def run_websockets_for_all_users():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = []

    for user_id, user_data in users.items():
        if 'd-token' in user_data:  # Real user with Discord enabled
            token = user_data['d-token']
            last[token] = None  # add token to the last dict
            tasks.append(listen_for_dms(token, user_id))

    if tasks:
        loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    # Start WebSocket listener in background thread
    ws_thread = Thread(target=run_websockets_for_all_users)
    ws_thread.start()

    # Start Flask itself
    app.run(debug=True)