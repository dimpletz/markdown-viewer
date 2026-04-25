from pathlib import Path
from html.parser import HTMLParser


class CoverageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_missed = False
        self.missed_lines = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "p" and attrs_dict.get("class") == "run mis":
            self.in_missed = True

    def handle_data(self, data):
        if self.in_missed:
            # Data like "96-97, 136-161, 164-171"
            for part in data.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-")
                    self.missed_lines.extend(range(int(start), int(end) + 1))
                elif part and part.isdigit():
                    self.missed_lines.append(int(part))

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_missed = False


files_to_check = [
    "z_5d1077e11535724a___main___py.html",
    "z_0b455751dbcd0010_database_py.html",
    "z_5d1077e11535724a_setup_py.html",
]

for f in files_to_check:
    path = Path(f"htmlcov/{f}")
    if path.exists():
        parser = CoverageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        print(f"{f}: missing lines count = {len(parser.missed_lines)}")
        if parser.missed_lines:
            print(f"  Sample: {parser.missed_lines[:10]}")
