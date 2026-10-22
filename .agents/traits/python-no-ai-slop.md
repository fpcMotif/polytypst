---
name: python-no-ai-slop
subject: Comments, docstrings, names, and error handling added or changed in project-owned Python code
requirement: 'Added code carries no AI slop: no comment or docstring that restates what the next line does, narrates the edit ("now we", "updated to", "new:"), or hedges; no placeholder or generic names (data, result, helper, temp, obj) where a domain name fits; no try/except that only logs and re-raises, swallows errors, or guards a call that cannot fail; no defensive isinstance or None checks on values an internal caller always supplies. A comment explains only why, in at most three lines.'
purpose: Generated filler hides the real behavior, inflates diffs, and makes the code read like a transcript instead of a program.
applicability: 'Applies to Python lines added or changed in a diff under src, tests, and scripts. Existing comments stay as written unless their code is removed. Validation at an input edge (CLI arguments, files, environment, network responses) is not defensive slop.'
guidance: Delete the restating comment and let the name carry the meaning; rename vague names to the domain term; let unexpected errors propagate.
---

```diff
-    # Loop over the pages and read each one
-    for p in pages:
-        try:
-            data = read_source_page(cache, p)
-        except Exception as e:
-            print(f"error: {e}")
-            raise
+    for number in pages:
+        page = read_source_page(cache, number)
```
