# Rename this file to secret.py and change the values
# User DB cannot be changed by clients at the moment, so they need to be added manually here
# Some fields may not be necessary for the server to function correctly

terms = "Your ToS text here"  # gets sent to each client upon login. You can change this to read from a file
wvhook = "https://discord.com/api/webhooks/blablabla"  # All messages to fake users are sent here
address = 'basement.of.moriya.moe'  # address of your server
port = 69  # port of your server

# Simulating a basic user database
users = {
    'wv:johndoe': {  # Real user to be used by a client
        'password': 'changeMe!',  # plaintext, could be changed to something like MD5
        'username': 'reimulover4',  # Discord username (only fill out when you want Discord functionality!)
        'token': 'reallylongandinterestingstring',  # Discord token (only fill out when you want Discord functionality!)
        'phone': '+420123456789',  # Signal phone number (only fill out when you want Signal functionality!)
        'session_id': None,
        'client_ids': [],
        'contact_lists': {
            'wv:johndoe/main'
        },
        'block_list': {},  # block and grant list functionality, only required for real users
        'grant_list': {},
        'default_contact_list': 'wv:johndoe/main',
        'presence': {
            'OnlineStatus': 'F',  # is the user logged-in?
            'UserAvailability': None,  # can be 'AVAILABLE', 'DISCREET' or None for invisible
            'StatusText': ''
        }
    },
    'wv:admin': {  # Fake user
        'password': 'null',  # null passwords are automatically denied client login
        'session_id': None,  # compatibility-only
        'client_ids': [],  # compatibility-only
        'contact_lists': {
            'wv:johndoe/main': 'InterVillage'  # defines the nickname in a contact list of someone else
        },
        'presence': {
            'OnlineStatus': 'F',
            'UserAvailability': None,
            'StatusText': 'the stupid ice fairy'
        }
    },
    'wv:wumpus': {  # Discord (fake) user
        'password': 'null',
        'session_id': None,
        'client_ids': [],
        'discord': '5489498468498498489',  # Recipient Discord user ID
        'contact_lists': {
            'wv:johndoe/main': 'D: Wumpus'
        },
        'presence': {
            'OnlineStatus': 'T',
            'UserAvailability': 'AVAILABLE',  # used to make the user appear as online in contact lists
            'StatusText': None
        }
    },
    'wv:signal': {  # Signal (fake) user
        'password': 'null',
        'session_id': None,
        'client_ids': [],
        'signal': '+420987654321',  # Recipient Signal phone number
        'contact_lists': {
            'wv:johndoe/main': 'S: Reimu'
        },
        'presence': {
            'OnlineStatus': 'T',
            'UserAvailability': 'AVAILABLE',
            'StatusText': None
        }
    }
}

ads = [  # List of random messages that get sent to every real online account every 30 minutes or so
    "You should check out Startpage, so that we can ditch Google once and for all!",
    "Arch Linux; NOW!"
]