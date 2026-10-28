from polytypst.books import module

bourbaki_heading = module("bourbaki", "spec").bourbaki_heading


def test_section_heading_uses_contents_title():
    assert bourbaki_heading("## 1. DIAGRAMS AND EXACT SEQUENCES", 1) == "## § 1. Diagrams and exact sequences"
    assert bourbaki_heading("# 7. THE APPROXIMATION THEOREM", 6) == "## § 7. Approximation theorem"


def test_section_footnote_marker_is_kept():
    assert bourbaki_heading("## 2. FLAT MODULES(*)", 1) == "## § 2. Flat modules (*)"


def test_numbered_subsection_becomes_level_three():
    assert bourbaki_heading("### 1. DIAGRAMS", 1) == "### 1. Diagrams"
    assert bourbaki_heading("## 2. M-FLAT MODULES", 1) == "### 2. M-flat modules"


def test_stray_running_head_is_dropped_and_body_text_kept():
    assert bourbaki_heading("# THE SNAKE DIAGRAM", 1) == ""
    assert bourbaki_heading("# EXERCISES", 1) == "## Exercises"
    assert bourbaki_heading("3. Let M be a module.", 1) is None
