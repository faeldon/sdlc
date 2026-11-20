# train-resolve

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

A landing train stacks ${count} changes on ${base} in this order, and stacking ${change} onto the change before it conflicts in: ${files}. Resolve each so every change in the train keeps what it was built to do: read each change's spec and diff with git show (reads only), edit only those files, run no other git command, then report what you kept from each side, ending with ## Evidence.

## deleted

${path} is deleted by ${side} (${commit}), and the other side changed it: `git diff ${base} ${kept} -- ${path}`, a read you may run, shows that change, and `git show :${stage}:${path}` the text it kept. Carry that change to where the content went, among the files the deleting commit added or changed, which you may edit too: ${moved}. Delete ${path} to keep the deletion, or keep the file only if its content still belongs there, and say which.

## change

- ${name}${this}: ${title}. Its spec: `git show ${pre}:${rel}/${spec}`; its diff: `git show ${pre}`.

## this

(this change)
