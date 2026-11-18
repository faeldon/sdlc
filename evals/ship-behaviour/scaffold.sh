#!/bin/sh
# The built-tier2 fixture, built by the suite's shared scaffold, with the run's home readied.
exec sh "$(dirname "$0")/../scaffold.sh" built-tier2 --sandbox
