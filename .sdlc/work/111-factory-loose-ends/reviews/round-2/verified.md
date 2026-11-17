- KEPT: code: C1: plugins/factory/scripts/factory.py:4249: `_up()` returns `True` (lost) when the port answered and `proc.poll()` shows the process exited, without probing the port with `_binds()`. A server that answered and then died on its own, leaving the port free, gets retried and recorded as a lost port. The exit-before-answering branch at line 4246 already does the probe. This post-loop branch needs `not _binds(host, port)`, plus a direct `_up()` test.

## Notes
I read `_binds`, `_up` and `_serve` and ran nothing. The change cites line 4246, but the defect is in the later branch at line 4249. The cited line already returns `not _binds(host, port)`, and the settled round-1 finding covers that branch. The report is still about a real, separate defect.

One edge case is small: a stray port answering together with the process exiting at the same moment. In that case the port won't bind, so it still reads as lost, which is correct.
