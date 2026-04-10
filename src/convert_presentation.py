import re

with open("gca_primer_project_presentation.md", "r", encoding="utf-8") as f:
    text = f.read()

# Add Marp frontmatter if not present
if not text.startswith("---\nmarp:"):
    frontmatter = """---
marp: true
theme: default
class: default
backgroundColor: white
---

"""
    text = frontmatter + text

# Remove "## スライドX: " prefix to make the heading clean
text = re.sub(r'(?m)^## スライド\d+:\s*(.*?)$', r'## \1', text)

with open("gca_primer_project_presentation.md", "w", encoding="utf-8") as f:
    f.write(text)
