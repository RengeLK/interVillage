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
        return app.xml_response({'Error': {'message': 'Session not found or invalid request'}}), 400

    ### !!! BROKEN !!! ###
    #if user != sender:
    #    return app.xml_response({'Error': {'message': 'Not authorized!'}}), 400

    content = {
        'SendMessage-Response': {
            'Result': {
                'Code': 200,
                'Description': 'nig'
            },
            'MessageID': 'cojavim4'
        }
    }

    # TODO: udelej neco s tou zpravou xd
    data = {
        'content': f'komu: {recipient}\nod: {sender}\nzprava: {msgcontent}\ntest kod lol'
    }

    webhook = "https://discord.com/api/webhooks/1292936265297301585/NnEP30QIVjhs1DJtwXrJlJuqZkTFDCemFjv6_HLbiEvBEwdiyNmSCoDgblrdVmAilIzy"
    send = requests.post(webhook, json=data)

    response = app.form_wv_message(content, transaction_id, session_id)
    return app.xml_response(response)