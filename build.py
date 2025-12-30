#!/usr/bin/env python3
import csv, re, subprocess
from pathlib import Path

csv_path = Path("/mnt/c/Users/Lucent/Downloads/substack/posts.csv")
posts_dir = Path("/mnt/c/Users/Lucent/Downloads/substack/posts")
out_md = Path("combined.md")
lua = Path("links-to-footnotes.lua")

titles_file = Path("titles.tsv")
titles = dict(line.rstrip("\n").split("\t", 1) for line in titles_file.read_text().splitlines()) if titles_file.exists() else {}

link_re = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")

parts = []

with open(csv_path, newline="", encoding="utf-8") as f:
	rows = list(csv.DictReader(f))

rows = [r for r in rows if r["is_published"].lower() == "true"]
rows.sort(key=lambda r: r["post_date"])

for r in rows:
	post_id = r["post_id"]
	title = r["title"]
	subtitle = r.get("subtitle", "")

	html = (posts_dir / f"{post_id}.html").read_text(encoding="utf-8")

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

	def repl(m):
		url = m.group(2)
		if url in titles:
			page_title = titles[url]
		else:
			print(f"fetching title for page {url}")
			html2 = subprocess.check_output(["curl", "-Ls", url], text=True)
			m2 = re.search(r'property=["\']og:title["\'][^>]*content=["\'](.*?)["\']', html2, re.I|re.S) or re.search(r"<title[^>]*>(.*?)</title>", html2, re.I|re.S)
			page_title = re.sub(r"\s+", " ", m2.group(1).strip())
			print(f"got the title of: {page_title}")
			titles[url] = page_title
			titles_file.open("a", encoding="utf-8").write(url + "\t" + page_title.replace("\t"," ").replace("\n"," ") + "\n")
		page_title = page_title.replace('"', '\\"')
		return f'[{m.group(1)}]({url} "{page_title}")'

	md = link_re.sub(repl, md)

	# per-post: links -> footnotes; put them at end of this post
	md = subprocess.check_output(
		["pandoc", "-f", "markdown", "-t", "markdown+footnotes",
		 "--reference-location=document", "--lua-filter", str(lua), "--wrap=none"],
		input=md,
		text=True,
	)

	parts.append(
		f"# {title}\n\n"
		+ (f"*{subtitle}*\n\n" if subtitle else "")
		+ md.strip()
		+ "\n\n"
	)

out_md.write_text("".join(parts), encoding="utf-8")
print(out_md)

