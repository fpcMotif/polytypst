---
name: python-efficient-hot-paths
subject: Loops, regexes, imports, file and JSON reads, and subprocess or I/O steps added or changed in project-owned Python code
requirement: 'Added code does not re-read the same file or re-parse the same JSON inside a loop; compiles a regex used in a loop or a frequently called function once at module level; does not build strings or lists by repeated concatenation inside a loop; runs independent subprocess or I/O steps through the pool the surrounding code already has instead of one after another; and keeps heavy imports (OCR, PDF, ML, network clients) off CLI startup paths by importing them inside the command that uses them.'
purpose: Book builds and parity checks touch hundreds of pages, so per-page waste multiplies into minutes, and slow imports make every CLI call slow.
applicability: 'Applies to Python lines added or changed in a diff under src, tests, and scripts. One-shot scripts and code that runs once per build are exempt from the regex and concatenation rules. The parallel rule applies only where a pool or executor already exists in the surrounding code.'
guidance: Hoist the read or parse above the loop; move re.compile to module scope; collect parts in a list and join once; submit independent steps to the existing pool; move the heavy import into the command function.
---

```diff
+_PAGE_MARK = re.compile(r"^% page (\d+)$")
+
 def page_marks(lines):
-    out = ""
-    for line in lines:
-        m = re.match(r"^% page (\d+)$", line)
-        if m:
-            out += m.group(1) + "\n"
-    return out
+    return "".join(m.group(1) + "\n" for line in lines if (m := _PAGE_MARK.match(line)))
```
