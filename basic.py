################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## basic.py - handle reqs     ##
## -renge 2024-2025           ##
################################
import app, poll
import uuid

def handle_login(login_request, transaction):
    user_id = login_request.get('UserID')
    #client_id = login_request.get('ClientID', {}).get('URL')
    password = login_request.get('Password')
    time_to_live = login_request.get('TimeToLive')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')

    # Check if the user exists and the password is correct
    if user_id in app.users and app.users[user_id]['password'] == password and password != 'null':
        # Generate a unique session ID for the user
        session_id = 'rs-' + str(uuid.uuid4())
        app.users[user_id]['session_id'] = session_id  # save it

        # Send ToS as a message from the admin (defined in secret.py)
        poll.send_message_to_queue(user_id, 'wv:admin', 'intro', app.terms)

        resp = {
            'Login-Response': {
                'UserID': user_id,
                'Result': app.form_status(200),
                'SessionID': session_id,
                'KeepAliveTime': time_to_live,
                'CapabilityRequest': 'T'
            }
        }
        response = app.form_wv_message(resp, transaction_id)
        return app.xml_response(response)

    # If login fails, return an error response
    resp = {
        'Login-Response': {
            'UserID': user_id if user_id else '',
            'Result': app.form_status(409)  # Invalid Password
        }
    }
    response = app.form_wv_message(resp, transaction_id)
    return app.xml_response(response)


def handle_logout(transaction, session):
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Find user by session_id
    user = None
    for u in app.users.values():
        if u['session_id'] == session_id:
            user = u
            break

    if user:
        user['session_id'] = None

        content = {
            'Disconnect': {
                'Result': app.form_status(200)
            }
        }

        response = app.form_wv_message(content, transaction_id)
        return app.xml_response(response)

    # Invalid session ID
    resp = app.form_wv_message({'Status': app.form_status(604)}, transaction_id, session_id)
    return app.xml_response(resp)


def handle_client_capability(capability_request, transaction, session):
    client_id = capability_request.get('ClientID', {}).get('URL')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Check if the client ID is associated with a valid user session
    user = None
    for u in app.users.values():
        if client_id in u['client_ids']:
            user = u
            break

    if user:
        # Respond with capabilities according to the specs
        # TODO: grab info from the response, no hard-code
        resp = {
            'ClientCapability-Response': {
                'ClientID': {
                    'URL': client_id  # Include the ClientID URL as specified
                },
                'CapabilityList': {
                    'ClientType': 'MOBILE_PHONE',
                    'InitialDeliveryMethod': 'P',
                    'AcceptedContentType': [
                        #'text/x-vCard; charset=utf-8',
                        #'text/x-vCalendar; charset=utf-8',
                        #'application/x-sms',
                        'text/plain; charset=utf-8'
                    ],
                    'AcceptedTransferEncoding': 'BASE64',
                    'AcceptedContentLength': 32767,
                    'SupportedBearer': ['HTTP'],
                    'MultiTrans': 1,
                    'ParserSize': 32767,
                    'SupportedCIRMethod': [
                            'WAPSMS',
                            'STCP'
                    ],
                    'TCPAddress': app.address,
                    'TCPPort': app.port,
                    'ServerPollMin': 10,
                    'DefaultLanguage': 'eng'
                }
            }
        }
        response = app.form_wv_message(resp, transaction_id, session_id)
        return app.xml_response(response)

    # If client ID is not found, return an error response
    resp = {
        'ClientCapability-Response': {
            'ClientID': {
                'URL': client_id
            },
                'Result': app.form_status(422)  # ClientID Mismatch
            }
    }
    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)


def handle_service_request(service_request, transaction, session):
    client_id = service_request.get('ClientID', {}).get('URL')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Is meant to only respond with features that the client requested, but the server *cannot* provide
    resp = {
        'Service-Response': {
            'ClientID': {
                'URL': client_id
            },
            'Functions': {
                'WVCSPFeat': {
                    'PresenceFeat': {}
                }
            },
            'AllFunctions': {
                'WVCSPFeat': {}
            }
        }
    }
    response = app.form_wv_message(resp, transaction_id, session_id)
    return app.xml_response(response)