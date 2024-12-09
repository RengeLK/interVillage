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
        resp = {
            'GetList-Response': {
                'ContactList': user['contact_lists'],
                'DefaultContactList': user['default_contact_list']
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)

    # Invalid session ID
    resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
    return app.xml_response(resp)


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

        resp = {
            'ListManage-Response': {
                'Result': app.form_status(200),
                'NickList': {
                    'NickName': nicknames
                },
                'ContactListProperties': {
                    'Property': contact_list_properties
                }
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)

    # Invalid session ID
    resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
    return app.xml_response(resp)

def handle_block_request(block_request, transaction, session):
    block_list = block_request.get('BlockList')
    grant_list = block_request.get('GrantList')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if user is None:
        # Invalid session ID
        resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
        return app.xml_response(resp)

    # BlockList management
    isUsed = block_list['InUse']
    addList = block_list['AddList']
    removeList = block_list['RemoveList']

    # Is block list used? If so, do stuff with it
    if isUsed == 'T':
        # Add users to the block list
        if addList:
            for blud, userID in addList.items():
                if userID in user['block_list']:
                    # User ID is already on the list
                    resp = app.form_wv_message({'Status': app.form_status(531)}, transaction_id, session_id)
                    return app.xml_response(resp)
                else:
                    user['block_list'][userID] = None

        # Remove users from the block list
        if removeList:
            for blud, userID in removeList.items():
                if userID in user['block_list']:
                    user['block_list'].pop(userID)
                else:
                    # User ID isn't in the block list, respond with error
                    resp = app.form_wv_message({'Status': app.form_status(531)}, transaction_id, session_id)
                    return app.xml_response(resp)


    # GrantList management (inverted block list logic)
    # TODO: actually do something with the grant list
    isUsed = grant_list['InUse']
    addList = grant_list['AddList']
    removeList = grant_list['RemoveList']

    # Is grant list used? If so, do stuff with it
    if isUsed == 'T':
        print(f"{user} tried setting a grant list, NOT IMPLEMENTED!!!!!!!!!!")


    response = app.form_wv_message({'Status': app.form_status(200)}, transaction_id, session_id)
    return app.xml_response(response)