import re

with open("gca_primer_project_presentation.md", "r", encoding="utf-8") as f:
    text = f.read()

# Add styling for scaling/fitting text
if "<style>" not in text:
    style_block = """<style>
section {
  font-size: 28px;
  padding: 40px;
}
h1 { font-size: 1.8em; }
h2 { font-size: 1.5em; }
h3 { font-size: 1.25em; }
pre, code {
  font-size: 0.85em;
  white-space: pre-wrap;
  word-wrap: break-word;
}
table { font-size: 0.9em; }
</style>
"""
    # Insert after the frontmatter
    text = re.sub(r'(---\n\n)', r'\1' + style_block + '\n', text, count=1)

with open("gca_primer_project_presentation.md", "w", encoding="utf-8") as f:
    f.write(text)
