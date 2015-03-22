Ellis - API Guide
=================

Ellis provides a RESTful API. This is used by the Web GUI and can also
be used by other clients. All access must go via this API, rather than
directly to the database.

Data formats
------------

By default, Ellis returns JSON to all requests.  It also supports the
more-efficient msgpack protocol by specifying header `Accept:
application/x-msgpack`. In most cases, POSTs support both JSON and
URL-encoded data (URL-encoded data may not be supported for data that
isn't "flat").  The client should specify the content type rather than
requiring the server to guess.

Client authentication
---------------------

In general, Ellis requires requests to be authenticated.  It will
reject requests that don't include an API key or an authentication
cookie.  The API key should be presented in the `NGV-API-Key` HTTP
header.

User accounts
=============

    /accounts/

POST to this URL to create a new account.  Does not require the API key but, to limit initial adoption it does require a header with a signup code in it: `NGV-Signup-Code`.

Body:

    {
      "username": <string>,
      "password": <string>,
      "full_name": <string>,
      "email": <string>
    }

Response:

 * 301 if the client specifies it would prefer a redirect to a status-code based response.
 * Otherwise:
   - 201 created on success
   - 409 conflict if the account already exists
   - 400 if the signup code is wrong or missing or some other field fails verification

As concessions to browser form posts:

 * The signup code map be specified as a field in the data body named `signup_code`
 * The client may specify URLs to redirect to on success/failure via URL parameters `onsuccess` / `onfailure`.

User account
============

    /accounts/<username>/

The <username> is just the email address of the account, URL-encoded.

DELETE to this URL to delete an account.  You must already have a session valid for the account to do this.

Response:

 * 204 No content on response
 * 5xx if an error occurs on the server

```
    /accounts/<username>/password
```

POST to this URL to set or recover the password. No valid session is required for this.

With no additional headers and an empty body, this requests system to send a password recovery email.

With the `NGV-Recovery-Token header` set to the correct password
recovery token and the new password in the body (as `text/plain`),
this requests the system to set the password to the specified value.

Response:

  * 200 OK if all goes well. Note that an unknown email address with no token will give this response too, for security reasons.
  * 400 if the token is expired, not set, or does not match, or a token is provided but the email address is unknown.
  * 503 Service Unavailable if the request has been throttled. `Retry-After:` is set appropriately.

Alternatively, browser support can be used - in this case the response
is 301, the token may be supplied in the recovery_token parameter, and
the password may be supplied in the password parameter.

Browser login
=============

    /session/

POST to this URL to create a new session.

Body:

    {
      "username": <string>,
      "password": <string>
    }

Response:

 * 301 if the client specifies it would prefer a redirect to a status-code based response.
 * Otherwise:
   - 201 created on success (including a secure cookie that authenticates the request)
   - 403 forbidden if the credentials are invalid

Number management
=================

    /accounts/<username>/numbers/
    /accounts/<username>/numbers/<SIP URI>/
    /accounts/<username>/numbers/<SIP URI>/password

Make an POST request to `/accounts/<username>/numbers/` to allocate a new number (chosen randomly from the pool) to an account. Optionally, specify the following parameters, either in the form-encoded body or as URL parameters:

      "private_id":       <private identity to associate this number with, null if none yet exists>
      "pstn":             <boolean specifying if number should be a PSTN>,

Note that `private_id` must be a private identity that already exists - if you specify an arbitrary one, Ellis will not create it for you. If you want to provision numbers and private identities of your own choosing, you should read "Provisioning specific numbers" below or use the [Homer](https://github.com/Metaswitch/crest/blob/dev/docs/homer_api.md) and [Homestead APIs](https://github.com/Metaswitch/crest/blob/dev/docs/homestead_api.md) directly.

Response

    {
      "formatted_number": <the phone number formatted for local display>,
      "gab_listed":       true if the the number is listed in the global address book,
      "number":           <the phone number, currently, this will be equal to the sip_username>,
      "pstn":             <boolean specifying if number is a PSTN>,
      "private_id":       <private identity associated with this number>
      "sip_password":     <a randomly-generated SIP password for the number, only available at creation>,
      "sip_uri":          <the SIP uri of the number>,
      "sip_username":     <the user portion of the SIP URI, i.e. exactly what the user should enter into the client>
    }

Make a GET request to `/accounts/<username>/numbers/` to retrieve
details for all numbers.  The format of an individual number is the
same as that returned at creation.  The list is wrapped in an object:

    {
      "numbers": [
      // ...
      ]
    }

The password is not available after creation so it is not included.

Make a DELETE request to `/accounts/<username>/numbers/<SIP URI>/`
to unallocate the number.  It is returned to the pool.

Make an empty post to `/accounts/<username>/numbers/<SIP
URI>/password` to generate a new password.  It is returned in the
response as the `sip_password` parameter.

Provisioning specific numbers
=================

Make an empty POST request to `/accounts/<username>/numbers/<SIP URI>/` to create that specific SIP URI. Note that:
  * Requests to this URI *must* have the NGV-API-Key header specified - this is not an operation that ordinary users can perform

Specify the following parameters, either in the form-encoded body or as URL parameters:

      "private_id":       <private identity to associate this number with>,
      "new_private_id":   <boolean specifying if private identity should be created>

The 'private_id' URL parameter is mandatory. This is assumed to be an existing private ID to associate the SIP URI with, unless the 'new_private_id' parameter is set to true, in which case this private ID will be created and the password returned.

Response is the same as for a POST to `/accounts/<username>/numbers/`.

Global Address Book
===================

    /accounts/<username>/numbers/<SIP URI>/listed
    /gab/

Make a PUT to `/accounts/<username>/numbers/<SIP URI>/listed/(1|0)`
to set the Global Address Book (GAB) listed flag (1 for "number is
listed", 0 for unlisted).

Make a GET request to `/gab/` to retrieve the whole Global Address
Book. The response has the following form:

    {
      "contacts": [
        {
          "email": "alice@example.com",
          "full_name": "Alice Example",
          "numbers": [
            "sip:6505550455@example.com"
          ]
        },
        {
          "email": "bob@example.com",
          "full_name": "Robert Example",
          "numbers": [
            "sip:6505550333@example.com",
            "sip:+16505550565@example.com"
          ]
        },
        // ...
      ]
    }

Simservs
========

    /accounts/<username>/numbers/<SIP URI>/simservs

Make a GET/PUT to `/accounts/<username>/numbers/<SIP URI>/simservs`
to set the simservs document. Ellis merely proxies the request onto Homer.

See the Homer [docs](https://github.com/Metaswitch/crest/blob/dev/docs/homer_api.md) for more information.

iFCs
====

    /accounts/<username>/numbers/<SIP URI>/ifcs

Make a GET/PUT to `/accounts/<username>/numbers/<SIP URI>/ifcs`
to set the iFC document. Ellis merely proxies the request onto Homestead.

See the Homestead [docs](https://github.com/Metaswitch/crest/blob/dev/docs/homestead_api.md) for more information.
