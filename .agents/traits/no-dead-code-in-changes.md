---
name: no-dead-code-in-changes
subject: Python functions, branches, parameters, variables, and imports added or changed in a diff
requirement: "Every added or changed function, branch, parameter, variable, and import has a live use: a caller, a reader, or an entry point. Code with no use is deleted, not kept for later."
purpose: Dead code left behind by generated or exploratory edits hides the real behavior and makes later changes slower and riskier.
applicability: Applies to project-owned Python source, scripts, and tests. Public API names and compatibility shims that external consumers still use count as live.
guidance: Confirm deadness through entry points and consumers (pyproject scripts, CLI wiring, tests, top-level scripts), not a single missing search hit.
---

```diff
-    zone = spec.header_zone_lines
-    in_zone = (spec.header_zone_lines is None and lines_so_far <= 2) or (
-        spec.header_zone_lines is not None and lines_so_far <= spec.header_zone_lines
-    )
-    if in_zone:
+    zone = spec.header_zone_lines
+    if lines_so_far <= (2 if zone is None else zone):
```
