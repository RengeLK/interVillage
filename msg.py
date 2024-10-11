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

def handle_send_message(send_message_request, transaction, session):
    recipient = send_message_request['MessageInfo']['Recipient']['User'].get('UserID')
    sender = send_message_request['MessageInfo']['Sender']['User'].get('UserID')
    msgcontent = send_message_request.get('ContentData')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if not user:
        # Invalid session ID
        resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
        return app.xml_response(resp)

    ### !!! BROKEN !!! ###
    #if user != sender:
    #    return app.xml_response({'Error': {'message': 'Not authorized!'}}), 400

    content = {
        'SendMessage-Response': {
            'Result': app.form_status(200),
            'MessageID': 'random4'
        }
    }

    # TODO: actually do something with this
    data = {
        'content': f'to: {recipient}\nfrom: {sender}\nmessage: {msgcontent}\nintervillage notification!'
    }

    webhook = "https://discord.com/api/webhooks/1292936265297301585/NnEP30QIVjhs1DJtwXrJlJuqZkTFDCemFjv6_HLbiEvBEwdiyNmSCoDgblrdVmAilIzy"
    send = requests.post(webhook, json=data)
    print(send.status_code)

    response = app.form_wv_message(content, transaction_id, session_id)
    return app.xml_response(response)