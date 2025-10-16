r"""
 _______________
| \     |       |
|   \   |       |
|     \ |       |
|-------\-------|
|       | \     |
|       |   \   |
|_______|_____\_|
"""

import time
import requests

# ==================================================
# Configurable Options
# ==================================================

USER_API_URL = "http://127.0.0.1:8000/api/users/"
LOGIN_API_URL = "http://127.0.0.1:8000/api/token/"
PROFILE_API_URL = "http://127.0.0.1:8000/api/user-profile/"

EMAIL_PREFIX = "testuser"
DOMAIN = "example.com"
PASSWORD = "testpassword"

# Toggle for unique passwords per user
# Set to True to append user index to PASSWORD
# Set to False to use the same PASSWORD for all users
UNIQUE_PASSWORDS = True

# Toggle whether to create profiles for new users
CREATE_PROFILES = True

# Toggle whether to use token from
# login response or user creation response
USE_LOGIN_TOKEN = True

# Starting index for user numbering
START = 1

# Number of users to create
COUNT = 5

USER_CREATION_DELAY = 0.1
LOGIN_DELAY = 0.2
PROFILE_CREATION_DELAY = 0.3

MAX_ERROR_DISPLAY = 10

# ==================================================
# ==================================================


class CreateTestUsers:
    """
    A test user creation utility for bulk user and profile generation.

    This class handles the automated creation of test users with optional
    profile creation, supporting both direct token extraction from user
    creation responses and separate login-based token retrieval.

    Attributes:
        verbose (bool): Enable detailed logging output.
        users_created (int): Counter for successfully created users.
        profiles_created (int): Counter for successfully created profiles.
        failed (int): Counter for failed operations.
        errors (list): List of tuples containing (email, error_message) for failed operations.
    """

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.users_created = 0
        self.profiles_created = 0
        self.failed = 0
        self.errors = []

    def __str__(self):
        return (
            f"CreateTestUsers: users_created = {self.users_created}, "
            f"profiles_created = {self.profiles_created}, "
            f"failed = {self.failed}"
        )

    __repr__ = __str__

    def wait(self, delay_name):
        """
        Apply a configured delay based on the operation type.

        Args:
            delay_name (str): Type of delay to apply. Valid values:
                - 'user': USER_CREATION_DELAY
                - 'login': LOGIN_DELAY
                - 'profile': PROFILE_CREATION_DELAY

        Note:
            If an invalid delay_name is provided, no delay is applied (0 seconds).
        """
        delays = {
            "user": USER_CREATION_DELAY,
            "login": LOGIN_DELAY,
            "profile": PROFILE_CREATION_DELAY,
        }
        time.sleep(delays.get(delay_name, 0))

    def short_text(self, text, limit=100):
        """
        Truncate text to a specified length with ellipsis if longer.

        Args:
            text (str): The text to potentially truncate.
            limit (int, optional): Maximum character length. Defaults to 100.

        Returns:
            str: Original text if within limit, otherwise truncated text with '...' appended.

        Example:
            >>> short_text("A very long error message...", limit=10)
            Output: 'A very lon...'
        """
        return text if len(text) <= limit else text[:limit] + "..."

    def log_line(self, message, level=0):
        """
        Log a message with hierarchical indentation.

        Outputs messages with indentation based on nesting level, making
        it easier to visualize operation hierarchy and flow.

        Args:
            message (str): The message to log.
            level (int, optional): Indentation level (0-based). Each level
                adds 4 spaces of indentation. Defaults to 0.

        Note:
            Logging only occurs if self.verbose is True.
        """
        if not self.verbose:
            return
        indent = " " * (4 * level)
        print(f"{indent}{message}")

    def login_user(self, email, password):
        """
        Authenticate a user and retrieve their access token via JWT.

        Performs a login request to the LOGIN_API_URL and extracts the
        access token from the response if successful.

        Args:
            email (str): User's email address.
            password (str): User's password.

        Returns:
            str or None: JWT access token if login successful, None otherwise.

        Note:
            Expects response structure: {"result": {"access": "token_string"}}
        """
        try:
            response = requests.post(
                LOGIN_API_URL, json={"email": email, "password": password}, timeout=10
            )
            if response.status_code in (200, 201):
                data = response.json()
                result = data.get("result", {})
                access = result.get("access")

                if access:
                    self.log_line(f"↳ [✓] Logged in: {email}", level=2)
                    return access
                else:
                    self.log_line(
                        f"↳ [x] Login failed (missing access token): {self.short_text(response.text)}",
                        level=2,
                    )
                    self.failed += 1
                    self.errors.append((email, response.text))
                    return None
            else:
                self.log_line(
                    f"↳ [x] Login failed: {response.status_code} {self.short_text(response.text)}",
                    level=2,
                )
                self.failed += 1
                self.errors.append((email, response.text))
                return None
        except Exception as e:
            self.log_line(f"↳ [!] Exception during login: {e}", level=2)
            self.failed += 1
            self.errors.append((email, str(e)))
            return None

    def create_user_profile(self, user_id, email, access_token):
        """
        Create a user profile for a newly created user account.

        Makes an authenticated POST request to PROFILE_API_URL to create
        a profile associated with the specified user ID.

        Args:
            user_id (str or int): The ID of the user for whom to create a profile.
            email (str): User's email address (used for logging only).
            access_token (str): JWT access token for authentication.

        Returns:
            bool: True if profile created successfully, False otherwise.

        Note:
            Profile creation includes ?w8=false parameter to disable
            w8 generation during the creation process.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        profile_data = {"user": user_id}
        profile_url = f"{PROFILE_API_URL}?w8=false"  # disable w8 generation

        try:
            response = requests.post(
                profile_url, json=profile_data, headers=headers, timeout=10
            )

            if response.status_code in (200, 201):
                self.log_line(f"↳ [✓] User profile created for {email}", level=2)
                self.profiles_created += 1
                return True
            else:
                self.log_line(
                    f"↳ [x] Failed to create profile: {response.status_code} {self.short_text(response.text)}",
                    level=2,
                )
                self.failed += 1
                self.errors.append((email, f"profile: {response.text}"))
                return False
        except Exception as e:
            self.log_line(f"↳ [!] Exception during profile creation: {e}", level=2)
            self.failed += 1
            self.errors.append((email, str(e)))
            return False

    def create_test_users(self):
        """
        Create multiple test users with optional profile creation.

        This method orchestrates the bulk creation of test users based on
        configuration settings. It handles user creation, authentication
        (via login or token extraction), and profile creation with
        appropriate delays between operations.

        The process for each user:
            1. Create user account via USER_API_URL
            2. If CREATE_PROFILES is True:
               - Get access token (via login or from creation response)
               - Create user profile via PROFILE_API_URL
            3. Apply configured delays between operations

        Configuration options used:
            - START: Starting index for user numbering
            - COUNT: Number of users to create
            - USE_LOGIN_TOKEN: Token source selection
            - CREATE_PROFILES: Enable/disable profile creation
            - UNIQUE_PASSWORDS: Use unique passwords per user
            - Various delay settings for rate limiting

        Returns:
            dict: Summary of operations containing:
                - users_created (int): Number of successfully created users
                - profiles_created (int): Number of successfully created profiles
                - failed (int): Number of failed operations
                - errors (list): List of (email, error_message) tuples

        Note:
            Existing users (detected via 400 status with "exist" in response)
            are skipped and not counted as failures.
        """
        self.log_line("=" * 50)
        self.log_line(f"Starting user creation: {COUNT} user(s) from index {START}")
        self.log_line("=" * 50 + "\n")

        self.log_line(
            f"Token source: {'Login API' if USE_LOGIN_TOKEN else 'User Creation API'}\n"
        )

        if not CREATE_PROFILES and USE_LOGIN_TOKEN:
            self.log_line(
                "[!] Warning: USE_LOGIN_TOKEN is True but CREATE_PROFILES is False\n"
            )

        for i in range(START, START + COUNT):
            email = f"{EMAIL_PREFIX}{i}@{DOMAIN}"

            if UNIQUE_PASSWORDS:
                password = f"{PASSWORD}{i}"
            else:
                password = PASSWORD

            user_data = {
                "email": email,
                "username": email,
                "password": password,
            }

            try:
                # ===== CREATE USER =====

                self.log_line(f"[.] Processing user {i - START + 1}/{COUNT}: {email}")

                response = requests.post(USER_API_URL, json=user_data, timeout=10)

                if response.status_code in (200, 201):
                    result = response.json()
                    user_result = result.get("result", {})
                    user_id = user_result.get("id")

                    if not user_id:
                        self.log_line(
                            f"↳ [!] Created user but couldn't find ID in response: {email}",
                            level=1,
                        )
                        self.failed += 1
                        continue

                    self.log_line(
                        f"↳ [✓] Created user: {email} (ID: '{user_id}') (Password: '{password}')",
                        level=1,
                    )
                    self.users_created += 1

                    if CREATE_PROFILES:
                        access_token = None

                        if USE_LOGIN_TOKEN:
                            # ===== LOGIN USER TO GET TOKEN =====

                            # Small delay to ensure user is
                            # fully created before login
                            self.wait("login")

                            self.log_line(
                                "↳ [.] Attempting login to get access token...",
                                level=1,
                            )
                            access_token = self.login_user(email, password)
                            if not access_token:
                                continue

                            # Small delay to ensure login process
                            # is complete before profile creation
                            self.wait("profile")
                        else:
                            # ===== USE TOKEN FROM USER CREATION RESPONSE =====

                            access_token = user_result.get("access")
                            if access_token:
                                self.log_line(
                                    "↳ [✓] Using access token from user creation response",
                                    level=1,
                                )
                            else:
                                self.log_line(
                                    f"↳ [x] Access token not found in user creation response for {email}",
                                    level=1,
                                )
                                self.failed += 1
                                self.errors.append(
                                    (email, "Missing access token in creation response")
                                )
                                continue

                        # ===== CREATE USER PROFILE =====

                        self.log_line(
                            "↳ [.] Attempting user profile creation...", level=1
                        )
                        profile_creation = self.create_user_profile(
                            user_id, email, access_token
                        )
                        if not profile_creation:
                            continue
                    else:
                        self.log_line(
                            "↳ [~] Skipped profile creation (disabled)", level=1
                        )
                elif response.status_code == 400 and "exist" in response.text.lower():
                    self.log_line(f"↳ [~] Skipped existing user: {email}", level=1)
                else:
                    self.log_line(
                        f"↳ [x] Failed for {email}: {response.status_code} {self.short_text(response.text)}",
                        level=1,
                    )
                    self.failed += 1
                    self.errors.append((email, response.text))
            except requests.RequestException as e:
                self.log_line(f"↳ [!] Network error for {email}: {e}", level=1)
                self.failed += 1
                self.errors.append((email, str(e)))
            except Exception as e:
                self.log_line(f"↳ [!] Unexpected error for {email}: {e}", level=1)
                self.failed += 1
                self.errors.append((email, str(e)))

            # Small delay before next user creation
            self.wait("user")

        # Summarize results
        self.log_line("\n" + "=" * 50)
        self.log_line(f"[✓] Users created: {self.users_created}")
        self.log_line(f"[✓] Profiles created: {self.profiles_created}")
        self.log_line(f"[x] Failed: {self.failed}")
        if self.errors:
            self.log_line(
                f"\nErrors (showing {min(MAX_ERROR_DISPLAY, len(self.errors))}):"
            )
            for email, msg in self.errors[:MAX_ERROR_DISPLAY]:
                self.log_line(f"- {email}: {self.short_text(msg, limit=200)}", level=1)
        self.log_line("=" * 50)

        # Return summary
        return {
            "users_created": self.users_created,
            "profiles_created": self.profiles_created,
            "failed": self.failed,
            "errors": self.errors,
        }


if __name__ == "__main__":
    try:
        creator = CreateTestUsers()
        creator.create_test_users()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
