# @file users.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging
import Crypto.Random
import uuid
import datetime
import base64

from metaswitch.ellis.data._base import AlreadyExists
from metaswitch.ellis.data._base import NotFound
from metaswitch.ellis import settings
from metaswitch.common import utils

_log = logging.getLogger("ellis.data")


def lookup_user_id(db_sess, email):
    cursor = db_sess.execute("""
                             SELECT user_id FROM users
                             WHERE email = :email;
                             """,
                             {"email": email})

    try:
        return cursor.fetchone()[0]
    except TypeError:
        _log.info("User email %s not found", email)
        raise NotFound
    finally:
        cursor.close()

def create_user(db_sess, password, full_name, email, expires):
    # Check if the user already exists.
    try:
        lookup_user_id(db_sess, email)
    except NotFound:
        pass
    else:
        _log.info("Email %s already exists", email)
        raise AlreadyExists()

    hashed_password = utils.hash_password(password)
    user_id = uuid.uuid4()

    expires_date = (datetime.datetime.now() + datetime.timedelta(days = expires)).strftime("%Y-%m-%d %H:%M:%S") if expires else None

    user = {
             "user_id": user_id,
             "hashed_password": hashed_password,
             "full_name": full_name,
             "email": email,
             "expires": expires_date
           }
    db_sess.execute("""
                   INSERT INTO users (user_id, password, full_name, email, expires)
                   VALUES (:user_id, :hashed_password, :full_name, :email, :expires)
                   """,
                   user)
    return user

def delete_user(db_sess, user_id):
    db_sess.execute("""
                   DELETE FROM users
                   WHERE user_id = :user_id
                   """,
                   {
                       "user_id": user_id
                   })

def get_user(db_sess, user_id):
    cursor = db_sess.execute("""
                             SELECT password, full_name, email, expires
                             FROM users
                             WHERE user_id = :user_id
                             """, {"user_id": user_id})
    try:
        hashed_password, full_name, email, expires = cursor.fetchone();
    finally:
        cursor.close()

    return {"user_id":         user_id,
            "hashed_password": hashed_password,
            "full_name":       full_name,
            "email":           email,
            "expires":         expires}

def get_user_by_email_and_password(db_sess, email, password):
    """Test if the password is correct, and retrieve the user record.

    Returns user (if correct) or None (if incorrect), where user is
    the record of data from the database.  In particular, user.email
    is the true email address from the database (which may differ in
    case or other collation-invariant ways from the supplied email).
    """
    cursor = db_sess.execute("""
                             SELECT user_id, password, full_name, email, expires FROM users
                             WHERE email = :email
                             """, {"email": email})

    try:
        user_id, hashed, full_name, true_email, expires = cursor.fetchone()
        _log.debug("User email %s (%s) has hashed password %r", email, true_email, hashed)
    except TypeError: # pragma: no cover
        # Deleted under our feet?
        _log.warning("User email %s not found", email)
        return None
    else:
        if utils.is_password_correct(password, hashed):
            return {"user_id":         user_id,
                    "hashed_password": hashed,
                    "full_name":       full_name,
                    "email":           true_email,
                    "expires":         expires}
        else:
            return None
    finally:
        cursor.close()

def _get_valid_token(db_sess, email):
    """Get the currently-valid password recovery token.

    Throws ValueError if email unknown, or NotFound if token not present or expired.
    """
    cursor = db_sess.execute("""
                             SELECT recovery_token, recovery_token_created FROM users
                             WHERE email = :email
                             """, {"email": email})

    try:
        token, created = cursor.fetchone()
        _log.debug("User %s has token %s created %s", email, token, created)
    except TypeError:
        # Email not known
        _log.warning("User %s not found", email)
        raise ValueError("User not found")
    finally:
        cursor.close()

    if not token:
        _log.info("Token not present")
        raise NotFound

    expiry = created + datetime.timedelta(seconds=settings.RECOVERY_TOKEN_LIFETIME_SECS)
    if datetime.datetime.now() >= expiry:
        _log.info("Token expired")
        raise NotFound

    _log.info("Token valid")
    return token

def get_token(db_sess, email):
    """Get a password recovery token if we can.

    Returns the token.  If the email address is unknown, throws
    ValueError.
    """
    try:
        token = _get_valid_token(db_sess, email)
    except NotFound:
        _log.info("Create new token")
        token = base64.b64encode(Crypto.Random.get_random_bytes(16))
        created = datetime.datetime.now()
        # @@@KSW There's a race here: if two requests arrive at once,
        # both will succeed but they'll set different tokens, so only
        # one of the resulting tokens will be valid.  We should really
        # be more transactional here.
        db_sess.execute("""
                        UPDATE users
                        SET recovery_token = :token,
                            recovery_token_created = :created
                        WHERE email = :email
                        """, {"token":   token,
                              "created": created,
                              "email":   email})
    return token

def get_details(db_sess, email):
    """Get the details of a user given their email address."""
    cursor = db_sess.execute("""
                             SELECT full_name, email FROM users
                             WHERE email = :email
                             """, {"email": email})

    try:
        full_name, true_email = cursor.fetchone()
        _log.debug("User %s has name %s", email, full_name)
    except TypeError:
        # Email not known
        _log.warning("User %s not found", email)
        raise ValueError("User not found")
    finally:
        cursor.close()

    return {"full_name": full_name,
            "email":     true_email}

def set_recovered_password(db_sess, email, token, password):
    """Use a password recovery token to set a new password.

    Checks the email address and token are correct, and sets the new
    password.  If the email address is unknown, throws ValueError.  If
    there is no token in the database, throws NotFound.  If the token
    is wrong, throws ValueError.
    """
    expected_token = _get_valid_token(db_sess, email)
    if token == expected_token:
        _log.warn("Set password for %s", email)
        hashed_password = utils.hash_password(password)
        db_sess.execute("""
                        UPDATE users
                        SET password = :hashed_password,
                            recovery_token = NULL,
                            recovery_token_created = NULL
                        WHERE email = :email
                        """, {"email": email,
                              "hashed_password": hashed_password}),
    else:
        raise ValueError('Wrong token')
