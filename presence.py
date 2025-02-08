################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## presence.py - presence     ##
## -renge 2024-2025           ##
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
        resp = app.form_wv_message({'Status': app.form_status(200)}, transaction_id, session_id)
        return app.xml_response(resp)

    # Invalid session ID
    resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
    return app.xml_response(resp)


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
        # Invalid session ID
        resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
        return app.xml_response(resp)

    # Find the owner of the contact list
    owner = None
    for uid, details in app.users.items():
        if contact_list_name in details.get('contact_lists', {}):
            owner = uid
            break

    if owner is None:
        # Nonexistent Contact List
        resp = app.form_wv_message({'Status': app.form_status(700)}, transaction_id, session_id)
        return app.xml_response(resp)

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

    # Prepare the response
    resp = {
        'GetPresence-Response': {
            'Result': app.form_status(200),
            'Presence': nicknames
        }
    }

    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)