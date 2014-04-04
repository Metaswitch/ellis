Available numbers configuration
===============================

The available numbers (from which new telephone numbers are assigned)
are stored in the database. The range of available numbers can be
initialized or updated using the `create_numbers.py` tool:

    sudo env/bin/python src/metaswitch/ellis/tools/create_numbers.py <options>

where the options are:

  * `--start <nnn>` to specify the initial directory number, e.g., 6505550000.
  * `--count <nnn>` to specify how many numbers should be made available, e.g., 1000.
  * `--pstn` (optional): if present, the command affects available PSTN numbers; if absent, it affects available internal numbers.
  * `--realm <name>` (optional): the realm in which the directory number resides; if absent, it defaults to the home domain.


