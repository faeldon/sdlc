VERDICT: PASS

I reviewed the whole diff from e26da2f, the commit the change was rebased onto. The change is Tier 1, so the intent's Approach stands in for a spec. The end-to-end path works. The drawer's markdown renderer does what the Outcome says, and hostile content comes out as text. I found no failure to raise as a CHANGE.

## Notes

- **Main hasn't moved.** `main` is still at e26da2f, so there is no commit on it outside the diff for the script to catch.
- **Gate.** `build/land-2.gate.md` reads `GATE: PASS`, 2340 passed, 13 skipped. I did not run the gate again. There is no `build/land-2.md` report; the only landing record is the gate file.
- **Checks.** There is no `checks.md` in the change folder, so there are no acceptance checks to read.
- **Rendering, checked against the Outcome.** I ran the page's own `h()` and markdown block under node, in a scratch directory, against the fixture's `005-draft-sharing/reviews/round-1/code.md`. Headings, paragraphs, task checkboxes (disabled, ticked or not), tables, fenced code, inline code, bold, italic and blockquotes all come out as the Outcome asks. A `spec.md` link resolves to a `data-path` link into the drawer. An `https` link opens in a new tab with `rel="noopener noreferrer"`. Frontmatter is set apart in a `pre`. The file list from `_files()` is recursive, so a link into a subfolder resolves.
- **Hostile input.** `<script>`, `<img onerror>`, `data:` and `javascript:` links, and `../` escapes all come out as text or as refused spans, never as markup or a live `href`.
- **Live server.** I served the fixture board on 127.0.0.1 from a scratch copy. `/file` returns the raw text of the `.md` file, so rendering is client-side as designed. The page contains the renderer. A path that escapes the folder gets a 404. I stopped that server afterwards. The board on port 5170 belongs to another session and I did not touch it.
- **`tests/test_board.py`.** 138 passed, 13 skipped, with the markdown, hostile-markup and focus-trap tests among them.
- **Minor, not a spec failure.** A link whose URL has parentheses, such as `https://…/Foo_(bar)`, cuts at the first `)`. The rest of the URL is lost, and a stray `)` shows in the text. The Outcome names no such link, so this is a Note, not a CHANGE. It could become a seed.
- **Settled, not re-raised.** The blank pane for an empty `.md` file (seed 2026-11-18-8), and the `show()` race where a slow fetch paints over a later file (bug 2026-11-18-9). The decisions D1–D5 in `decisions.md` are ticked and settled.
- **Not run by me.** I did not drive the drawer in a browser, so the 390px layout, the focus trap and the Raw toggle are not checked by me. The builder's round-2 Chromium evidence reports them, and I have not re-run it. The screenshots never open the drawer (D5), which is the person's call and already settled.

## Evidence

$ git log --oneline -n 8 && git merge-base HEAD main; git rev-parse e26da2f…; git diff --stat e26da2f…HEAD
2bf608a The board renders a change's markdown files
e26da2f Close 126-is-read-refuses-writers
… 40 files changed, 1416 insertions(+), 8 deletions(-)
exit: 0

$ git diff e26da2f…HEAD -- scripts/board.html docs/REFERENCE.md
(read: the renderer, `paint()`, `show()`, link click handler and `trapTab()` filter; REFERENCE line 540 adds the Raw toggle and link text)
exit: 0

$ cat decisions.md decision.md build/round-2.md reviews/land-1/code.md
(read: D1–D5 ticked; decision.md ESCALATE from the prior run; land-1 code review PASS)
exit: 0

$ git diff --name-only e26da2f…HEAD | grep -n draft
39:tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md
exit: 0

$ git log --oneline e26da2f..main; echo "main=$(git rev-parse main)"; git diff --stat e26da2f main | tail -3
main=e26da2f9880b866386029fe360eba7ef05013696
(no commits; no diff)
exit: 0

$ git diff e26da2f…HEAD -- tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md
(read: the fixture gains a rendered-markdown body: a link, a checklist, a table, a fenced block, a blockquote)
exit: 0

$ tail -5 build/land-2.gate.md; grep "GATE\|passed" build/land-2.gate.md
GATE: PASS
2340 passed, 13 skipped in 157.55s
exit: 0

$ which node && node --version
node
v26.13.0
exit: 0

$ cat notes.md; cat reviews/round-2/verified.md
(read: the two settled items; verified.md KEPT C1 for the empty-file pane)
exit: 0

$ node $D/probe.js scripts/board.html tests/fixtures/board/changes/005-draft-sharing/reviews/round-1/code.md "reviews/round-1/code.md" "spec.md,reviews/round-1/code.md,plan.md"
<p>VERDICT: PASS</p>
<h5 class="md-h2">Notes</h5>
<p>Fine. The share link … <a href="#" data-path="spec.md">the spec</a> …</p>
<ul><li class="md-task"><input … checked…></input>A saved draft gets a link.</li> … </ul>
<div class="md-table" tabindex="0" role="region" aria-label="table"><table>…</table></div>
<pre class="md-code" … aria-label="code"><code>def share_url(draft: Draft) -&gt; str: …</code></pre>
<blockquote><p>A note for the next round…</p></blockquote>
exit: 0

$ node $D/probe.js scripts/board.html $D/hostile.md "reviews/round-1/code.md" "spec.md,reviews/round-1/code.md"
<pre class="md-front">id: 124 / status: &lt;b&gt;x&lt;/b&gt;</pre>
<h4 class="md-h1">Title &lt;script&gt;alert(1)&lt;/script&gt;</h4>
<p>&lt;img src=x onerror=alert(1)&gt; and &lt;script&gt;bad()&lt;/script&gt;</p>
<ul><li class="md-task"><input disabled=""></input><span class="md-refused" title="not followed: javascript:alert(1">js</span>) …</li> … <a href="https://example.com/a?b=1" target="_blank" rel="noopener noreferrer">web</a> … <a href="mailto:a@b.c" …>mail</a></li></ul>
<p><span class="md-refused" title="not followed: data:text/html,<b>x</b>">data</span> <span class="md-refused" …>ok</span> <span class="md-refused" …>here</span></p>
<pre class="md-code" …><code>&lt;script&gt;x&lt;/script&gt;</code></pre>
exit: 0

$ node $D/probe.js scripts/board.html $D/empty.md "x.md" "x.md"
(no output)
exit: 0

$ node $D/probe.js scripts/board.html $D/ord.md "x.md" "x.md"
<ol start="3"><li>third</li><li>fourth wrapped under four</li></ol>
<p>Some <em>em</em> and <em>under</em> and snake_case_name and <del>gone</del> text.</p>
exit: 0

$ PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py
……… 138 passed, 13 skipped in 78.87s
exit: 0

$ PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py -k "markdown or focus or sink or hostile" -v | grep -E "PASS|FAIL|ERROR"
(no lines matched)
exit: 0

$ mkdir -p $D/fx && cp -R tests/fixtures/board/changes/. $D/fx/ && (sh tests/fixtures/board/serve.sh $D/fx 8765 &); curl state.json loop
(empty; first attempt gave up before the server was ready)
exit: 0

$ cat $D/serve.log; ps aux | grep "board --port"
{ "url": "http://127.0.0.1:8765/", "serving": true }
pid 28714: …/scripts/sdlc.py board --port 8765
exit: 0

$ curl -s http://127.0.0.1:8765/state.json | head -c 500
{"board": "sdlc", "repo": "drafts", "trunk": "main", … "changes": [{"change": "001-draft-labels", …}]}
exit: 0

$ curl -s "http://127.0.0.1:8765/file?change=005-draft-sharing&path=reviews/round-1/code.md" | head -4
VERDICT: PASS
## Notes
exit: 0

$ curl -s http://127.0.0.1:8765/ | grep -c renderMarkdown
2
exit: 0

$ curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8765/file?change=005-draft-sharing&path=../../../../etc/passwd"
404
exit: 0

$ kill 28714
exit: 0

$ sed -n 290,306p scripts/board.py
(read: `_files()` uses rglob, relative posix paths, so nested review files are listed)
exit: 0

$ PYTHONDONTWRITEBYTECODE=1 uv run --group dev pytest -q -p no:cacheprovider tests/test_board.py -k "nested or subfolder or reviews or link"
2 passed, 149 deselected in 3.70s
exit: 0
