import re

with open("gca_primer_project_presentation.md", "r", encoding="utf-8") as f:
    text = f.read()

# Update frontmatter to 16:9
text = re.sub(r'backgroundColor: white\n---', r'backgroundColor: white\nsize: 16:9\n---', text)

# Update style block to make font slightly smaller and padding smaller to fit more text
new_style = """<style>
section {
  font-size: 24px;
  padding: 30px 50px;
  justify-content: start;
}
h1 { font-size: 1.5em; margin-top: 10px; margin-bottom: 20px; }
h2 { font-size: 1.3em; margin-top: 10px; margin-bottom: 20px; }
h3 { font-size: 1.1em; margin-top: 10px; margin-bottom: 10px; }
p, ul, ol { margin-bottom: 10px; }
pre, code {
  font-size: 0.8em;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin-bottom: 15px;
}
table { font-size: 0.9em; }
</style>"""

text = re.sub(r'<style>.*?</style>', new_style, text, flags=re.DOTALL)

with open("gca_primer_project_presentation.md", "w", encoding="utf-8") as f:
    f.write(text)
