#!/usr/bin/env python3
import csv, re, subprocess
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

substack_dir = Path("/mnt/c/Users/Lucent/Downloads/substack")
out_md = Path("output/combined.md")
chapters_dir = Path("output/chapters")
lua = Path("links-to-footnotes.lua")

chapters_dir.mkdir(parents=True, exist_ok=True)

titles_file = Path("data/footnotes.tsv")
titles = dict(line.rstrip("\n").split("\t", 1) for line in titles_file.read_text().splitlines()) if titles_file.exists() else {}

# Parts: chapter_num -> (title, description) inserted before that chapter
parts_file = Path("data/parts.tsv")
part_breaks = {}
if parts_file.exists():
	for line in parts_file.read_text().splitlines():
		if line.strip() and not line.startswith("#"):
			cols = line.split("\t")
			num = int(cols[0])
			title = cols[1] if len(cols) > 1 else ""
			desc = cols[2] if len(cols) > 2 else ""
			part_breaks[num] = (title, desc)

# Extract URLs for title fetching (not for replacement)
url_re = re.compile(r"https?://[^\s\)\]\"'>]+")

parts = []
chapter_files = []

with open(substack_dir / "posts.csv", newline="", encoding="utf-8") as f:
	rows = list(csv.DictReader(f))

rows = [r for r in rows if r["is_published"].lower() == "true"]
rows.sort(key=lambda r: r["post_date"])

for chapter_num, r in enumerate(rows, 1):
	post_id = r["post_id"]
	title = r["title"]
	subtitle = r.get("subtitle", "")

	html = (substack_dir / "posts" / f"{post_id}.html").read_text(encoding="utf-8")

	md = subprocess.check_output(
		["pandoc", "-f", "html", "-t", "markdown", "--wrap=none"],
		input=html,
		text=True,
	)

	# cut anything after the last horizontal rule (drops subscribe/footer)
	lines = md.splitlines()
	cut = max((i for i,l in enumerate(lines) if re.match(r"-{4,}$", l)), default=None)
	lines = lines[:cut]
	lines = [l for l in lines if l.strip() not in ("<div>", "</div>")]
	md = "\n".join(lines)

	# Convert Substack LaTeX blocks to standard math
	def latex_repl(m):
		expr = m.group(1).replace("\\\\", "\\").replace("\\\\", "\\").replace("\\n", "")
		return f"$${expr}$$"
	md = re.sub(r'::: \{\.latex-rendered attrs="\{\\"persistentExpression\\":\\"([^"]+)\\"[^}]+\}" component-name="LatexBlockToDOM"\}\s*:::', latex_repl, md)

	# Replace characters the subset font lacks
	md = md.replace("\u2011", "-")  # non-breaking hyphen
	md = md.replace("ℝ", r"$\mathbb{R}$")  # real numbers

	# Fetch titles for URLs not yet in titles.tsv (Lua filter uses these)
	for url in url_re.findall(md):
		if "lucent.substack.com" in url:
			continue
		if url not in titles:
			print(f"fetching title for page {url}")
			try:
				html2 = subprocess.check_output(["curl", "-Ls", url], text=True, timeout=10)
				m2 = re.search(r'property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html2, re.I|re.S) or re.search(r"<title[^>]*>(.*?)</title>", html2, re.I|re.S)
				if m2:
					page_title = re.sub(r"\s+", " ", m2.group(1).strip())
					print(f"got the title of: {page_title}")
					titles[url] = page_title
					titles_file.open("a", encoding="utf-8").write(url + "\t" + page_title.replace("\t"," ").replace("\n"," ") + "\n")
			except:
				pass

	# Drop cap on first paragraph
	def drop_cap(m):
		first, rest = m.group(1), m.group(2)
		return f"\\lettrine{{{first}}}{{}}{rest}"
	md = re.sub(r"^([A-Z])(\w+)", drop_cap, md.strip(), count=1)

	slug = r["post_id"].split(".", 1)[1]

	# Insert part break before this chapter if specified
	part_header = ""
	if chapter_num in part_breaks:
		part_title, part_desc = part_breaks[chapter_num]
		part_header = f"\\part{{{part_title}}}\n"
		if part_desc:
			part_header += f"\\partdesc{{{part_desc}}}\n"
		part_header += "\n"

	content = (
		part_header
		+ f"# {title}\n\n"
		+ (f"*{subtitle}*\n\n" if subtitle else "")
		+ md
		+ "\n\n"
	)
	parts.append(content)

	# Write individual chapter file
	# Convert to Pacific time before extracting date - posts were written before midnight PT
	post_dt = datetime.strptime(r["post_date"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
	post_date = post_dt.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
	chapter_file = chapters_dir / f"{post_date}-{slug}.md"
	chapter_file.write_text(content, encoding="utf-8")
	chapter_files.append(str(chapter_file))
	print(f"Wrote: {chapter_file}")

out_md.write_text("".join(parts), encoding="utf-8")
print(f"\nWrote {out_md} with {len(parts)} chapters")
print(f"Wrote {len(chapter_files)} individual files to {chapters_dir}/")

