################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## app.py - main file         ##
## -renge 2024                ##
################################
from flask import Flask, request
import xmltodict
import secret, basic, poll, list, presence, msg  # import all other files

app = Flask(__name__)

# TODO: implement NewMessage (and, like, everything else)
# TODO: cleanup comments after my boy chatgpt
# TODO: fix ALL the error codes using your brand new form_status func
# TODO: rewrite all responses to use form_wv_message

# Import secrets here so I don't have to rewrite everything
users = secret.users

# Terms of Use text (a simple message)
terms_of_use = "By using this service, you agree to the following terms: [...]"

# Regular browser visitors
@app.route('/', methods=['GET'])
def root():
    return 'you need an imps client to connect to intervillage\n-renge 2024'

# Actual IMPS route
@app.route('/imps', methods=['POST'])
def imps():
    # Convert XML body to a Python dictionary
    try:
        imps_data = xmltodict.parse(request.data)
        print("Received IMPS request:", request.data)
    except:
        resp = form_wv_message(form_status(503, 'Unknown request type'), 0)
        return xml_response(resp)

    # Check for specific request types
    if 'WV-CSP-Message' in imps_data:
        return handle_wv_csp_message(imps_data['WV-CSP-Message'])
    resp = form_wv_message(form_status(501), 0)
    return xml_response(resp)

def handle_wv_csp_message(message_request):
    session = message_request.get('Session', {})
    transaction = session.get('Transaction', {})
    transaction_content = transaction.get('TransactionContent', {})

    # Handle Login-Request
    if 'Login-Request' in transaction_content:
        return basic.handle_login(transaction_content['Login-Request'], transaction)

    # Handle Logout-Request
    elif 'Logout-Request' in transaction_content:
        return basic.handle_logout(transaction, session)

    # Handle ClientCapability-Request
    elif 'ClientCapability-Request' in transaction_content:
        return basic.handle_client_capability(transaction_content['ClientCapability-Request'], transaction, session)

    # Handle Service-Request
    elif 'Service-Request' in transaction_content:
        return basic.handle_service_request(transaction_content['Service-Request'], transaction, session)

    # Handle KeepAlive-Request
    elif 'KeepAlive-Request' in transaction_content:
        return poll.handle_keep_alive_request(transaction_content['KeepAlive-Request'], transaction, session)

    # Handle GetList-Request
    elif 'GetList-Request' in transaction_content:
        return list.handle_get_list_request(transaction, session)

    # Handle ListManage-Request
    elif 'ListManage-Request' in transaction_content:
        return list.handle_list_manage_request(transaction_content['ListManage-Request'], transaction, session)

    # Handle UpdatePresence-Request
    elif 'UpdatePresence-Request' in transaction_content:
        return presence.handle_update_presence_request(transaction_content['UpdatePresence-Request'], transaction, session)

    # Handle GetPresence-Request
    elif 'GetPresence-Request' in transaction_content:
        return presence.handle_get_presence_request(transaction_content['GetPresence-Request'], transaction, session)

    # Handle SendMessage-Request
    elif 'SendMessage-Request' in transaction_content:
        return msg.handle_send_message(transaction_content['SendMessage-Request'], transaction, session)

    # Unknown request type
    else:
        resp = form_wv_message(form_status(501), transaction['TransactionDescriptor']['TransactionID'])
        return xml_response(resp)


def form_status(code: int, desc = None):
    codes = {
        200: 'Success',
        201: 'Partially Successful',
        202: 'Accepted',

        400: 'Bad Request',
        401: 'Unauthorized',
        402: 'Bad Parameter',
        403: 'Forbidden/Bad Login',
        404: 'Not Found',  # Wow, how surprising...
        405: 'Service Not Supported',
        409: 'Invalid Password',
        415: 'Unsupported Media Type',
        420: 'Invalid Transaction',  # fani
        422: 'ClientID Mismatch',
        423: 'Invalid InvitationID',
        426: 'Invalid MessageID',
        431: 'Unauthorized Group',

        500: 'Server Error',  # nig
        501: 'Not Implemented',
        503: 'Service Unavailable',
        504: 'Timeout',
        506: 'Service Not Agreed',
        516: 'Domain Forwarding Not Supported',
        531: 'Unknown User',
        532: 'Recipient Blocked Sender',
        536: 'Too Many Hits',
        538: 'Message Rejected',  # by recipient
        540: 'Header Encoding Not Supported',

        600: 'Session Expired',
        601: 'Forced Logout',  # by server
        604: 'Invalid Session',  # doesn't exist
        605: 'New Value Not Accepted',  # KeepAlive

        700: 'Nonexistent Contact List',
        701: 'Contact List Already Exists',
        702: 'Invalid User Properties',
        750: 'Invalid Presence Attribute',
        751: 'Invalid Presence Value',
        # Skipping 8xx: Groups
        900: 'Multiple Errors'
    }

    if not desc:
        desc = codes[code]
    resp = {
        'Status': {
            'Code': code,
            'Description': desc
        }
    }
    return resp


def form_wv_message(content: dict, transaction_id, session_id = None):
    if session_id:
        ses = {
            'SessionType': 'Inband',
            'SessionID': session_id
        }
    else: ses = { 'SessionType': 'Outband' }

    response = {
        'WV-CSP-Message': {
            'Session': {
                'SessionDescriptor': ses,
                'Transaction': {
                    'TransactionDescriptor': {
                        'TransactionMode': 'Response',
                        'TransactionID': transaction_id,
                        'Poll': 'F'
                    },
                    'TransactionContent': {}
                }
            }
        }
    }

    response['WV-CSP-Message']['Session']['Transaction']['TransactionContent'] = content
    return response

def xml_response(data_dict):
    xml_data = xmltodict.unparse(data_dict, pretty=True, full_document=True)
    # Manually add the xmlns
    xml_data = xml_data.replace('<WV-CSP-Message>', '<WV-CSP-Message xmlns="http://www.wireless-village.org/CSP1.1">')
    xml_data = xml_data.replace('<TransactionContent>', '<TransactionContent xmlns="http://www.wireless-village.org/TRC1.1">')
    xml_data = xml_data.replace('<PresenceSubList>', '<PresenceSubList xmlns="http://www.wireless-village.org/PA1.1">')
    return xml_data, 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    app.run(debug=True)
