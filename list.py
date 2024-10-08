################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## list.py - handle contacts  ##
## -renge 2024                ##
################################
import app

def handle_get_list_request(transaction, session):
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if user:
        # Respond with the user's contact lists and default contact list
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
                            'GetList-Response': {
                                'ContactList': user['contact_lists'],
                                'DefaultContactList': user['default_contact_list']
                            }
                        }
                    }
                }
            }
        }
        return app.xml_response(response)

    return app.xml_response({'Error': {'message': 'Session not found'}}), 400


def handle_list_manage_request(list_manage_request, transaction, session):
    contact_list = list_manage_request.get('ContactList')
    defaultCL = 'F'
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')
    if 'Default' in contact_list:
        defaultCL = 'T'

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if user:
        nicknames = []
        for n, u in app.users.items():
            if contact_list in u['contact_lists']:
                if n not in contact_list:
                    nicknames.append({'Name': u['contact_lists'][contact_list], 'UserID': n})

        contact_list_properties = [
            {'Name': 'DisplayName', 'Value': contact_list},
            {'Name': 'Default', 'Value': defaultCL}
        ]

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
                            'ListManage-Response': {
                                'Result': {
                                    'Code': 200
                                },
                                'NickList': {
                                    'NickName': nicknames
                                },
                                'ContactListProperties': {
                                    'Property': contact_list_properties
                                }
                            }
                        }
                    }
                }
            }
        }

        return app.xml_response(response)

    return app.xml_response({'Error': {'message': 'Session not found'}}), 400