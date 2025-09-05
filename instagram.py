################################
## InterVillage Project       ##
## Connecting IMPS and        ##
## modern IM platforms        ##
##                            ##
## instagram.py - ig helper   ##
## -renge 2024-2025           ##
################################
## Written by Claude, modified
## UNUSED, I discarded it since it shadowbanned accounts and I don't want to risk suspension lol
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

class Instagram:
    def __init__(self, data_dir: str = "~/.config/instagrapi", auto_load_session: bool = True):
        """Initialize Instagram library wrapper

        Args:
            data_dir: Directory to store session data
            auto_load_session: Automatically load existing session if available
        """
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.session_file = self.data_dir / "session.json"
        self.username_file = self.data_dir / "username.txt"

        self.client = Client()
        self.username = None
        """self.client.set_locale("cs_CZ")
        self.client.set_country("CZ")
        self.client.set_country_code(420)
        self.client.set_timezone_offset(2 * 60 * 60)  # CEST (UTC+2)
        self.client.set_user_agent("Mozilla/5.0 (Android 15; Mobile; rv:142.0) Gecko/142.0 Firefox/142.0")"""

        # Configure logging to be less verbose
        logging.getLogger('instagrapi').setLevel(logging.WARNING)

        # Auto-load session if requested and available
        if auto_load_session:
            self.load_session()

    def load_session(self) -> bool:
        """Load existing session if available

        Returns:
            bool: True if session loaded successfully, False otherwise
        """
        if not self.session_file.exists() or not self.username_file.exists():
            return False

        try:
            with open(self.username_file, 'r') as f:
                self.username = f.read()

            self.client.load_settings(self.session_file)
            return True
        except Exception as e:
            print(f"Loading session failed! {e}")
            return False

    def save_session(self) -> bool:
        """Save current session

        Returns:
            bool: True if session saved successfully, False otherwise
        """
        try:
            with open(self.username_file, 'w') as f:
                f.write(self.username)

            self.client.dump_settings(self.session_file)
            #os.chmod(self.session_file, 0o600)
            return True
        except Exception as e:
            print(f"Saving session failed! {e}")
            return False

    def login(self, username: str, password: str, verification_code: Optional[str] = None) -> bool:
        """Authenticate with Instagram

        Args:
            username: Instagram username
            password: Instagram password
            verification_code: 2FA code if required

        Returns:
            bool: True if login successful, False otherwise

        Raises:
            TwoFactorRequired: If 2FA code is needed but not provided
            ChallengeRequired: If Instagram requires additional verification
        """
        try:
            self.client.login(username, password, verification_code=verification_code)
            self.username = username
            self.save_session()
            return True

        except TwoFactorRequired:
            if not verification_code:
                raise TwoFactorRequired("Two-factor authentication code required")
            return False

        except ChallengeRequired:
            raise ChallengeRequired("Challenge required. Complete challenge in Instagram app and try again.")

        except Exception as e:
            print(f"Failed to login! {e}")
            return False

    def logout(self) -> bool:
        """Logout and clear session

        Returns:
            bool: True if logout successful, False otherwise
        """
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            if self.username_file.exists():
                self.username_file.unlink()
            self.username = None
            return True
        except Exception as e:
            print(f"Failed to logout! {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if currently authenticated

        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            self.client.account_info()
            return True
        except Exception as e:
            print("Auth check failed! ", e)
            return False

    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID from username

        Args:
            username: Instagram username

        Returns:
            Optional[int]: User ID if found, None otherwise
        """
        try:
            user_info = self.client.user_info_by_username(username)
            return int(user_info.pk)
        except Exception as e:
            print(f"Failed to get user ID! {e}")
            return None

    def get_username(self, user_id: int) -> Optional[str]:
        """Get username from user ID

        Args:
            user_id: Instagram user ID

        Returns:
            Optional[str]: Username if found, None otherwise
        """
        try:
            user_info = self.client.user_info(str(user_id))
            return user_info.username
        except Exception as e:
            print(f"Failed to get username! {e}")
            return None

    def send_message(self, recipient: str, message: str) -> bool:
        """Send a direct message

        Args:
            recipient: Username or user ID of recipient
            message: Message text to send

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_authenticated():
            return False

        # Check if recipient is a user ID or username
        if recipient.isdigit():
            user_id = int(recipient)
        else:
            user_id = self.get_user_id(recipient)
            if not user_id:
                return False

        try:
            self.client.direct_send(message, [user_id])
            return True
        except Exception as e:
            print(f"Failed to send message! {e}")
            return False

    def send_message_to_thread(self, thread_id: str, message: str) -> bool:
        """Send a message to a specific thread

        Args:
            thread_id: Instagram thread ID
            message: Message text to send

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_authenticated():
            return False

        try:
            self.client.direct_send(message, thread_ids = [int(thread_id)])
            return True
        except Exception as e:
            print(f"Failed to send thread message! {e}")
            return False

    def get_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent direct messages across all threads

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List[Dict]: List of message dictionaries with keys:
                - thread_id: Thread identifier
                - message_id: Message identifier
                - user_id: Sender's user ID
                - username: Sender's username
                - text: Message text (or '[Media/Other]' for non-text)
                - timestamp: Message timestamp
                - is_sent_by_viewer: True if sent by authenticated user
        """
        if not self.is_authenticated():
            return []

        try:
            # Get more threads and more messages per thread to ensure we catch recent messages
            threads = self.client.direct_threads(amount=20)
            messages = []

            for thread in threads:
                # Get more messages per thread (up to 20)
                try:
                    thread_info = self.client.direct_thread(int(thread.id), amount=20)
                    for msg in thread_info.messages:
                        messages.append({
                            'thread_id': thread.id,
                            'message_id': msg.id,
                            'user_id': msg.user_id,
                            'username': getattr(msg.user, 'username', 'Unknown'),
                            'text': msg.text or '[Media/Other]',
                            'timestamp': msg.timestamp,
                            'is_sent_by_viewer': msg.user_id == self.client.user_id
                        })
                except Exception:
                    # Skip threads that fail to load
                    continue

            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            return messages[:limit]

        except Exception as e:
            print(f"Failed getting messages! {e}")
            return []

    def get_thread_messages(self, thread_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get messages from a specific thread

        Args:
            thread_id: Instagram thread ID
            limit: Maximum number of messages to retrieve

        Returns:
            List[Dict]: List of message dictionaries (same format as get_messages)
        """
        if not self.is_authenticated():
            return []

        try:
            thread_info = self.client.direct_thread(int(thread_id), amount=limit)
            messages = []

            for msg in thread_info.messages:
                messages.append({
                    'thread_id': thread_id,
                    'message_id': msg.id,
                    'user_id': msg.user_id,
                    'username': getattr(msg.user, 'username', 'Unknown'),
                    'text': msg.text or '[Media/Other]',
                    'timestamp': msg.timestamp,
                    'is_sent_by_viewer': msg.user_id == self.client.user_id
                })

            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            return messages

        except Exception as e:
            print(f"Failed getting thread messages! {e}")
            return []

    def get_threads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get direct message threads

        Args:
            limit: Maximum number of threads to retrieve

        Returns:
            List[Dict]: List of thread dictionaries with keys:
                - thread_id: Thread identifier
                - participants: List of participant usernames
                - last_activity: Timestamp of last activity
                - has_unread: True if thread has unread messages
        """
        if not self.is_authenticated():
            return []

        try:
            threads = self.client.direct_threads(amount=limit)
            thread_list = []

            for thread in threads:
                # Get participants
                participants = []
                for user in thread.users:
                    participants.append(user.username)

                thread_list.append({
                    'thread_id': thread.id,
                    'participants': participants,
                    'last_activity': thread.last_activity_at,
                    'has_unread': not thread.read_state
                })

            return thread_list

        except Exception as e:
            print(f"Failed getting threads! {e}")
            return []

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account information

        Returns:
            Optional[Dict]: Account info dictionary or None if not authenticated
        """
        if not self.is_authenticated():
            return None

        try:
            info = self.client.account_info()
            return {
                'user_id': info.pk,
                'username': info.username
                # Others removed cuz useless and nonexistent
            }
        except Exception as e:
            print(f"Error in info! {e}")
            return None

# Export main classes and functions
__all__ = ['Instagram', 'TwoFactorRequired', 'ChallengeRequired']