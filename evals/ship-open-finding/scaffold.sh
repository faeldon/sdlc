#!/bin/sh
# The built-open-finding fixture, built by the suite's shared scaffold, with the run's home readied.
exec sh "$(dirname "$0")/../scaffold.sh" built-open-finding --sandbox
