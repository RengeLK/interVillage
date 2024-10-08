################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## basic.py - handle reqs     ##
## -renge 2024                ##
################################
import app
import uuid

# Function to handle login requests
def handle_login(login_request, transaction):
    user_id = login_request.get('UserID')
    #client_id = login_request.get('ClientID', {}).get('URL')
    password = login_request.get('Password')
    time_to_live = login_request.get('TimeToLive')

    # Check if the user exists and the password is correct
    if user_id in app.users and app.users[user_id]['password'] == password:
        # Generate a new unique session ID for the user
        session_id = str(uuid.uuid4())  # Generating a unique SessionID
        app.users[user_id]['session_id'] = session_id  # Store session ID

        # Respond with terms of use and a successful login response
        response = {
            'WV-CSP-Message': {
                'Session': {
                    'SessionDescriptor': {
                        'SessionType': 'Outband'
                    },
                    'Transaction': {
                        'TransactionDescriptor': {
                            'TransactionMode': 'Response',
                            'TransactionID': transaction.get('TransactionDescriptor', {}).get('TransactionID'),
                            'Poll': 'F'
                        },
                        'TransactionContent': {
                            'Login-Response': {
                                'UserID': user_id,
                                'Result': {
                                    'Code': 200,
                                    'Description': 'test success'
                                },
                                'SessionID': session_id,
                                #'TermsOfUse': terms_of_use,
                                'KeepAliveTime': time_to_live,
                                'CapabilityRequest': 'T'
                            }
                        }
                    }
                }
            }
        }
        return app.xml_response(response)

    # If login fails, return an error response
    response = {
        'WV-CSP-Message': {
            'Session': {
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction.get('TransactionDescriptor', {}).get('TransactionID')
                    },
                    'TransactionContent': {
                        'Login-Response': {
                            'UserID': user_id if user_id else '',
                            'Result': {
                                'Code': 401,
                                'Description': 'Invalid username or password'
                            }
                        }
                    }
                }
            }
        }
    }
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
                'Result': {
                    'Code': 200
                }
            }
        }

        response = app.form_wv_message(content, transaction_id)
        return app.xml_response(response)

    return app.xml_response({'Error': {'message': 'Session not found'}}), 400


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
                            'Poll': 'F'  # Assuming 'F' indicates no polling required
                        },
                        'TransactionContent': {
                            'ClientCapability-Response': {
                                'ClientID': {
                                    'URL': client_id  # Include the ClientID URL as specified
                                },
                                'CapabilityList': {
                                    'ClientType': 'MOBILE_PHONE',
                                    'InitialDeliveryMethod': 'P',
                                    'AcceptedContentType': [
                                        'text/plain; charset=utf-8',
                                        'application/x-sms',
                                        'text/x-vCard; charset=utf-8',
                                        'text/x-vCalendar; charset=utf-8'
                                    ],
                                    'AcceptedTransferEncoding': 'BASE64',
                                    'AcceptedContentLength': 32767,
                                    'SupportedBearer': ['HTTP'],
                                    'MultiTrans': 1,
                                    'ParserSize': 32767,
                                    'SupportedCIRMethod': [
                                        'WAPSMS',
                                        'WAPUDP',
                                        'SUDP',
                                        'STCP'
                                    ],
                                    'UDPPort': 4040,
                                    'TCPAddress': 'iv.renge4.net',
                                    'TCPPort': 4040,
                                    'ServerPollMin': 3
                                }
                            }
                        }
                    }
                }
            }
        }
        return app.xml_response(response)

    # If client ID is not found, return an error response
    response = {
        'WV-CSP-Message': {
            'Session': {
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction.get('TransactionDescriptor', {}).get('TransactionID'),
                        'Poll': 'F'
                    },
                    'TransactionContent': {
                        'ClientCapability-Response': {
                            'ClientID': {
                                'URL': client_id
                            },
                            'Result': {
                                'Code': 400,
                                'Description': 'Client ID not found'
                            }
                        }
                    }
                }
            }
        }
    }
    return app.xml_response(response)


def handle_service_request(service_request, transaction, session):
    client_id = service_request.get('ClientID', {}).get('URL')
    transaction_id = transaction.get('TransactionDescriptor', {}).get('TransactionID')
    session_id = session.get('SessionDescriptor', {}).get('SessionID')

    # Assuming the server supports the same features requested by the client
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
                        'Service-Response': {
                            'ClientID': {
                                'URL': client_id
                            },
                            'Functions': {
                                'WVCSPFeat': {
                                    'FundamentalFeat': {
                                        #'SearchFunc': {}
                                    },
                                    #'PresenceFeat': {},  # Assuming server supports Presence feature
                                    'IMFeat': {}  # Assuming server supports IM (Instant Messaging) feature
                                }
                            },
                            'AllFunctions': {
                                'WVCSPFeat': {}
                            }
                        }
                    }
                }
            }
        }
    }
    return app.xml_response(response)
# TODO: uhh it should respond with funcs the server DOESN'T support