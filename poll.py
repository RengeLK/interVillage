################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## poll.py - handle polling   ##
## -renge 2024                ##
################################
import app

def handle_keep_alive_request(keep_alive_request, transaction, session):
    time_to_live = keep_alive_request.get('TimeToLive')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Respond to the keep-alive request with a success message and KeepAliveTime
    resp = {
        'KeepAlive-Response': {
            'Result': {
                'Code': 200,
                'Description': 'Successfully completed.'
            },
            'KeepAliveTime': time_to_live
        }
    }
    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)