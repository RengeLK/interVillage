################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## poll.py - handle polling   ##
## -renge 2024-2025           ##
################################
import app
import time
from datetime import datetime

def handle_keep_alive_request(keep_alive_request, transaction, session):
    time_to_live = keep_alive_request.get('TimeToLive')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Only accept values below or equal 10 seconds
    if int(time_to_live) <= 10:
        resp = {
            'KeepAlive-Response': {
                'Result': app.form_status(200),
                'TimeToLive': int(time_to_live)
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)
    else:
        resp = {
            'KeepAlive-Response': {
                'Result': app.form_status(605),
                'KeepAliveTime': 10
            }
        }
    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)


message_queue = []  # dirty, but it works
def send_message_to_queue(recipient, sender, message_id, content, type = 'text/plain; charset=utf-8', encoding = 'None'):
    message_queue.append({
        'recipient': recipient,
        'sender': sender,
        'message_id': message_id,
        'content': content,
        'type': type,
        'encoding': encoding
    })

def handle_polling_request(session):
    session_id = session.get('SessionDescriptor', {}).get('SessionID')
    user = None
    for i, u in app.users.items():
        if u['session_id'] == session_id:
            user = i
            break
    if not user:
        # Invalid session ID
        resp = app.form_wv_message({'Status': app.form_status(604)}, 0, session_id)
        return app.xml_response(resp)
    timeout = 10  # maximum time to keep the connection open (in seconds)
    poll_interval = 1  # how often to check for new messages (in seconds)
    index = 0

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if there is a new message in the message queue
        if message_queue:
            new_message = message_queue[index]  # Get the first message in the queue
            recipient = new_message['recipient']
            if user != recipient:
                index += 1
                continue  # not an intended message
            sender = new_message['sender']
            message = new_message['content']
            length = len(message)
            message_id = new_message['message_id']
            type = new_message['type']
            encoding = new_message['encoding']

            if sender in app.users[recipient]['block_list']:
                message_queue.pop(index)  # do not forward messages from blocked users
                continue

            resp = {
                'NewMessage': {
                    'MessageInfo': {
                        'MessageID': message_id,
                        'ContentType': type,
                        'ContentEncoding': encoding,
                        'ContentSize': length,
                        'Recipient': {'User': {'UserID': recipient}},
                        'Sender': {'User': {'UserID': sender}},
                        'DateTime': datetime.now().isoformat(),
                        'Validity': 600
                    },
                    'ContentData': message
                }
            }

            message_queue.pop(index)  # clear the sent message
            response = app.form_wv_message(resp, 0, session_id)
            return app.xml_response(response)

        # Sleep for a short period before checking again
        time.sleep(poll_interval)

    # If no new messages, return a no-content response
    resp = app.form_wv_message({'Status': app.form_status(504)}, 0, session_id)
    return app.xml_response(resp)