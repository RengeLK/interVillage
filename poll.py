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

    # Only accept values below or equal 60 seconds
    if int(time_to_live) <= 60:
        resp = {
            'KeepAlive-Response': {
                'Result': app.form_status(200),
                'KeepAliveTime': int(time_to_live)
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