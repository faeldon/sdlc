#!/bin/sh
# The tier2-plan fixture, built by the suite's shared scaffold, with the run's home readied.
exec sh "$(dirname "$0")/../scaffold.sh" tier2-plan --sandbox
