################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## presence.py - presence     ##
## -renge 2024                ##
################################
import app

def handle_update_presence_request(update_presence_request, transaction, session):
    presence_sub_list = update_presence_request.get('PresenceSubList', {})
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if user:
        # Update OnlineStatus
        online_status = presence_sub_list.get('OnlineStatus', {})
        if online_status.get('Qualifier') == 'T':
            user['presence'] = {
                'OnlineStatus': online_status.get('PresenceValue') == 'T'
            }

        # Update UserAvailability
        user_availability = presence_sub_list.get('UserAvailability', {})
        if user_availability.get('Qualifier') == 'T':
            user['presence']['UserAvailability'] = user_availability.get('PresenceValue')

        # Update StatusText
        status_text = presence_sub_list.get('StatusText', {})
        if status_text.get('Qualifier') == 'T':
            user['presence']['StatusText'] = status_text.get('PresenceValue', '')
        else:
            user['presence']['StatusText'] = ''  # Set to empty if Qualifier is F

        # Prepare the response
        resp = app.form_wv_message(app.form_status(200), transaction_id, session_id)
        return app.xml_response(resp)

    return app.xml_response({'Error': {'message': 'Session not found or invalid request'}}), 400


def handle_get_presence_request(get_presence_request, transaction, session):
    contact_list_name = get_presence_request.get('ContactList')
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

    # Find the owner of the contact list
    owner = None
    for uid, details in app.users.items():
        if contact_list_name in details.get('contact_lists', {}):
            owner = uid
            break

    if owner is None:
        return app.xml_response({'Error': {'message': 'Contact list not found'}}), 400

    # Prepare the response
    response = {
        'WV-CSP-Message': {
            'Session': {
                'SessionDescriptor': {
                    'SessionType': 'Inband',
                    'SessionID': session_id
                },
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction_id,
                        'Poll': 'F'
                    },
                    'TransactionContent': {
                        'GetPresence-Response': {
                            'Result': {
                                'Code': 200,
                                'Description': 'Successfully completed.'
                            },
                            'Presence': []
                        }
                    }
                }
            }
        }
    }

    # Collect nicknames and presence details of users in the contact list
    nicknames = []
    for n, u in app.users.items():
        if contact_list_name in u['contact_lists']:
            if n != owner:  # Skip the owner of the list
                nicknames.append({
                    'UserID': n,
                    'PresenceSubList': {
                        'OnlineStatus': {
                            'Qualifier': 'T' if u['presence'].get('OnlineStatus') == 'T' else 'F',
                            'PresenceValue': u['presence'].get('OnlineStatus', 'F')
                        },
                        'UserAvailability': {
                            'Qualifier': 'T' if u['presence'].get('UserAvailability') else 'F',
                            'PresenceValue': u['presence'].get('UserAvailability', '')
                        },
                        'StatusText': {
                            'Qualifier': 'T' if u['presence'].get('StatusText') else 'F',
                            'PresenceValue': u['presence'].get('StatusText', '')
                        }
                    }
                })

    # Add nicknames and presence info to the response
    response['WV-CSP-Message']['Session']['Transaction']['TransactionContent']['GetPresence-Response']['Presence'] = nicknames

    return app.xml_response(response)