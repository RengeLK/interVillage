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

    # Only accept values below or equal 600 seconds (10 minutes)
    if time_to_live <= 600:
        resp = {
            'KeepAlive-Response': {
                'Result': app.form_status(200),
                'KeepAliveTime': time_to_live
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)
    else:
        resp = {
            'KeepAlive-Response': {
                'Result': app.form_status(605),
                'KeepAliveTime': 600
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)