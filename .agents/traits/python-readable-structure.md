---
name: python-readable-structure
subject: Control flow, functions, classes, loops, and names added or changed in project-owned Python code
requirement: 'Added code uses early returns or guard clauses instead of nesting more than two levels deep; adds no one-use wrapper function or class whose job a plain function or direct call can do; iterates with comprehensions, direct for loops, enumerate, or zip instead of range(len(...)) index loops; and uses one plain name for one meaning within a module.'
purpose: Flat, direct code with stable names is faster to read, review, and change than nested or indirected code.
applicability: 'Applies to Python lines added or changed in a diff under src, tests, and scripts. An index loop is allowed when the loop needs the index for arithmetic on neighbouring elements or mutates the sequence by position. A class is allowed when it holds state across calls or implements a protocol.'
guidance: Invert the condition and return early; inline the one-use wrapper at its caller; replace the index loop with enumerate or zip; rename the second spelling to the first.
---

```diff
-def page_labels(pages):
-    labels = []
-    for i in range(len(pages)):
-        if pages[i].number is not None:
-            if pages[i].label:
-                labels.append(pages[i].label)
-    return labels
+def page_labels(pages):
+    return [page.label for page in pages if page.number is not None and page.label]
```
