# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## _drop_record's docstring says what it returns, whole

Only a revert of the docstring brings back the half sentence "Why not, or".

```sh
python3 -I -c 'import ast,sys; t=ast.parse(open("scripts/sdlc.py").read()); d=next(ast.get_docstring(n) for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=="_drop_record"); sys.exit(0 if "Why not, or\nNone" not in d and "Returns why" in d else 1)'
```

## No docstring calls the change folder work/

Only a revert puts the pre-1.4.0 name back; the one docstring that means the old folder
(`_seed_title`'s ` → work/<folder>` pointer, which older intents hold) is allowed.

```sh
python3 -I -c 'import ast,re,sys; t=ast.parse(open("scripts/sdlc.py").read()); bad=[(getattr(n,"name","<module>"),l) for n in ast.walk(t) if isinstance(n,(ast.Module,ast.FunctionDef,ast.ClassDef)) for l in (ast.get_docstring(n) or "").splitlines() if re.search(r"(?<![\w./-])work/",l) and "→ work/" not in l]; print(*bad,sep="\n"); sys.exit(1 if bad else 0)'
```

## The module docstring points at -h instead of listing subcommands

Only a revert brings back the list that drifted from the parser.

```sh
python3 -I -c 'import ast,re,sys; d=ast.get_docstring(ast.parse(open("scripts/sdlc.py").read())); sys.exit(0 if "sdlc.py -h" in d and not re.search(r"^    (status|new|check|close|retro-commit) {2,}", d, re.M) else 1)'
```
