#!/bin/sh
# The set-up fixture with a product doc, built by the suite's shared scaffold, with the run's home
# readied: no factory is enabled there, so the question is the one asked without it.
exec sh "$(dirname "$0")/../scaffold.sh" product --sandbox
