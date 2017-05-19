# @file __init__.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

# Importing helper exceptions so that users of the package don't need to know
# the package structure
from metaswitch.ellis.data._base import NotFound, AlreadyExists # noqa
