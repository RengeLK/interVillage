################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## msg.py - handle messages   ##
## -renge 2024                ##
################################
import app
import requests
import subprocess

def handle_send_message(send_message_request, transaction, session):
    recipient = send_message_request['MessageInfo']['Recipient']['User'].get('UserID')
    sender = send_message_request['MessageInfo']['Sender']['User'].get('UserID')
    msgcontent = send_message_request.get('ContentData')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Only here to check SessionID
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break
    if not user:
        # Invalid session ID
        resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
        return app.xml_response(resp)


    if 'discord' in app.users[recipient]:
        ### Discord sending ###
        recipient_id = app.users[recipient]['discord']
        token = app.users[sender]['d-token']
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.71 Chrome/128.0.6613.36 Electron/32.0.0 Safari/537.36"
        }

        # create/fetch dm channel id
        url = "https://discord.com/api/v9/users/@me/channels"
        json_data = {
            "recipient_id": recipient_id
        }
        response = requests.post(url, headers=headers, json=json_data)
        channel_id = response.json().get('id')

        # actually send message to found channel id
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        json_data = {
            "content": msgcontent,
            "flags": 0,
            "mobile_network_type": "unknown"
        }
        requests.post(url, headers=headers, json=json_data)
    elif 'signal' in app.users[recipient]:
        ### Signal sending ###
        recipient_number = app.users[recipient]['signal']
        sender_number = app.users[sender]['phone']
        if recipient_number:
            command = [
                "signal-cli", "-a", sender_number, "send", "-m", msgcontent, recipient_number
            ]
            try:
                # Run the command to send the message
                subprocess.run(command, check=True)
                print(f"Signal message sent successfully to {recipient_number}!")
                return True  # Indicate success
            except subprocess.CalledProcessError as e:
                print(f"Failed to send Signal message: {e}")
                return False  # Indicate failure
    else:
        ### Fake user, send to #wv channel ###
        data = {
            'content': f'To: {recipient}\nFrom: {sender}\nMessage: {msgcontent}\nFrom InterVillage, an IMPS server by @renge4'
        }
        webhook = app.wvhook  # The older plaintext one is deleted, no need to try and abuse it :)
        requests.post(webhook, json=data)

    # final response to client, confirming the message
    content = {
        'SendMessage-Response': {
            'Result': app.form_status(200),
            'MessageID': 'random4'  # not going to bother with that right now
        }
    }
    response = app.form_wv_message(content, transaction_id, session_id)
    return app.xml_response(response)