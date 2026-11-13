#!/bin/sh
# The shipped fixture, built by the suite's shared scaffold, with the run's home readied.
exec sh "$(dirname "$0")/../scaffold.sh" shipped --sandbox
