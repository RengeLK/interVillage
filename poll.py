################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## poll.py - handle polling   ##
## -renge 2024                ##
################################
import app
import time

def handle_keep_alive_request(keep_alive_request, transaction, session):
    time_to_live = keep_alive_request.get('TimeToLive')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Only accept values below or equal 60 seconds
    if int(time_to_live) <= 60:
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
                'KeepAliveTime': 60
            }
        }
    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)


# TODO: Redo the polling system for individual platforms and make queues part of the user DB
message_queue = []
def send_message_to_queue(recipient, sender, message_id, content):
    message_queue.append({
        'recipient': recipient,
        'sender': sender,
        'message_id': message_id,
        'content': content
    })

def handle_polling_request(session):
    session_id = session.get('SessionDescriptor', {}).get('SessionID')
    timeout = 10  # maximum time to keep the connection open (in seconds)
    poll_interval = 2  # how often to check for new messages (in seconds)

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if there is a new message in the message queue
        if message_queue:
            new_message = message_queue.pop(0)  # Get the first message in the queue
            recipient = new_message['recipient']
            sender = new_message['sender']
            message = new_message['content']
            length = len(message)
            message_id = new_message['message_id']

            resp = {
                'NewMessage': {
                    'MessageInfo': {
                        'MessageID': message_id,
                        'ContentType': 'text/plain; charset=utf-8',
                        'ContentEncoding': 'None',
                        'ContentSize': length,
                        'Recipient': {'User': {'UserID': recipient}},
                        'Sender': {'User': {'UserID': sender}},
                        'DateTime': 'unused',
                        'Validity': 600
                    },
                    'ContentData': message
                }
            }

            response = app.form_wv_message(resp, 0, session_id)
            return app.xml_response(response)

        # Sleep for a short period before checking again
        time.sleep(poll_interval)

    # If no new messages, return a no-content response
    resp = app.form_wv_message({'Status': app.form_status(504)}, 0, session_id)
    return app.xml_response(resp)