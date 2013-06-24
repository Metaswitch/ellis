Ellis Feature List
==================

Ellis is a Web front-end to Homestead (HSS) and Homer (XDMS). It
provides the following features:

Users
-----

Ellis manages a database of *users*. A user has a name, email address,
password, and zero or more numbers. Users are an Ellis-only concept,
and are not exposed to the rest of the system.

Users can self-provision: anyone with the signup key can create a user
account.

Users can be configured as demo accounts, in which case they are
automatically expired (along with all their numbers) after one week.

Users can log into Ellis and create or configure their numbers.

If a user forgets their password, Ellis provides an email-based
password recovery mechanism.

Numbers
-------

Ellis manages a database of *numbers*. Each number is either available
for use, or belongs to a user. Numbers may be internal or PSTN
numbers, and may or may not be exposed in the global address book.

Ellis provides a command-line tool for provisioning the pool of
numbers available for use.

Users can self-provision their own numbers, either internal or PSTN,
and can control which of their numbers (if any) are exposed in the
global address book.

Global Address Book
-------------------

Ellis provides a global address book which lists each user, with
their full name, email address and exposed numbers.

Homestead
---------

When a number is assigned to a user in Ellis, Ellis creates a
corresponding private and public user identity (IMPI and IMPU) in
Homestead (the Clearwater HSS cache).

Ellis generates a secure password for the new private identity, stores
it in Homestead, and reveals it once to the user (without storing it).

Ellis provides the ability to reset the password to a new value (e.g.,
if the user has forgotten it).

When a number is deleted in Ellis, Ellis deletes it from Homestead as
well.

Ellis also sets the Initial Filter Criteria (iFCs) for the number to a
default value, specifying the use of Clearwater's built-in MMTEL
application server.

By editing the /usr/share/clearwater/ellis/web-content/js/app-servers.json
file, additional user-configurable application servers can be added. This file
maps user-friendly application-server names (e.g. "Voicemail server") to an
InitialFilterCriteria XML node, which will be added to or removed from the list
of iFCs on Homestead as the ser selects or unselects it in the configuration
dialog.

Homer
-----

When a number is assigned to a user in Ellis, Ellis creates a
corresponding configuration record in Homer (the Clearwater
XDMS). This record is a simservs document, and is intended for
built-in MMTEL application server.

Ellis provides a UI that allows the user to manipulate this
configuration record for each of their numbers. The features that can
be configured are all those supported by the built-in MMTEL
application server, i.e.,:

* Originating Identification Presentation (OIP) and Originating
  Identification Restriction (OIR). Whether or not to reveal my caller
  ID on calls I originate.

* Communication Diversion (CDIV), aka Call Diversion.
  * Whether call diversion is enabled.
  * The timeout after which a call should be considered not answered.
  * Zero or more forwarding rules, each of which specifies a number to forward to under certain conditions. Conditions are an AND of zero or more of:
    * No answer.
    * Busy.
    * Unregistered.
    * Unreachable.
    * Call has audio.
    * Call has video.

* Communication Barring (CB), aka Call Barring. Incoming and outgoing
  call barring is configured independently.
  * Incoming call barring: off, or all calls barred.
  * Outgoing call barring: off, international calls barred, or all calls barred.

When a number is deleted in Ellis, Ellis deletes the configuration
record from Homer as well.
