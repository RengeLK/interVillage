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
    stat_code = 200

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
        try:
            token = app.users[sender]['token']  # this is what the try statement is for (is sender capable of dc?)
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
            reimu = requests.post(url, headers=headers, json=json_data)
            # if something went wrong discord-side, change stat code
            if reimu.status_code != 200:
                stat_code = 500
        except KeyError as e:  # something wasn't found in db
            print(f'Discord sending error for {sender}: {e}')
            stat_code = 500
    elif 'signal' in app.users[recipient]:
        ### Signal sending ###
        recipient_number = app.users[recipient]['signal']
        try:
            sender_number = app.users[sender]['phone']  # is sender capable of signal?
            if recipient_number:
                command = [
                    "./signal", "-a", sender_number, "send", "-m", msgcontent, recipient_number
                ]
                try:
                    # Run the command to send the message
                    subprocess.run(command, check=True)
                    print(f"Signal message sent successfully to {recipient_number}!")
                except subprocess.CalledProcessError as e:
                    print(f"Failed to send Signal message: {e}")
                    stat_code = 500
        except KeyError:  # sender isn't signal-capable
            print(f'{sender} tried sending a Signal message to {recipient} without being capable!')
            stat_code = 500
    else:
        ### Fake user, send to #wv channel ###
        data = {
            'content': f'To: {recipient}\nFrom: {sender}\nMessage: {msgcontent}\nFrom InterVillage, an IMPS server by @renge4'
        }
        webhook = app.wvhook
        requests.post(webhook, json=data)

    # final response to client, confirming the message
    content = {
        'SendMessage-Response': {
            'Result': app.form_status(stat_code),
            'MessageID': 'random4'  # TODO: message IDs everywhere!
        }
    }
    response = app.form_wv_message(content, transaction_id, session_id)
    return app.xml_response(response)