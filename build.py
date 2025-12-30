#!/usr/bin/env python3
import csv, re, subprocess
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

substack_dir = Path("/mnt/c/Users/Lucent/Downloads/substack")
out_md = Path("combined.md")
chapters_dir = Path("chapters")
lua = Path("links-to-footnotes.lua")

chapters_dir.mkdir(exist_ok=True)

titles_file = Path("titles.tsv")
titles = dict(line.rstrip("\n").split("\t", 1) for line in titles_file.read_text().splitlines()) if titles_file.exists() else {}

link_re = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")

parts = []
chapter_files = []

with open(substack_dir / "posts.csv", newline="", encoding="utf-8") as f:
	rows = list(csv.DictReader(f))

rows = [r for r in rows if r["is_published"].lower() == "true"]
rows.sort(key=lambda r: r["post_date"])

for r in rows:
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

	def repl(m):
		url = m.group(2)
		# Skip title fetch for internal links (handled specially in Lua filter)
		if "lucent.substack.com" in url:
			return m.group(0)
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

	content = (
		f"# {title}\n\n"
		+ (f"*{subtitle}*\n\n" if subtitle else "")
		+ md.strip()
		+ "\n\n"
	)
	parts.append(content)

	# Write individual chapter file
	# Convert to Pacific time before extracting date - posts were written before midnight PT
	post_dt = datetime.strptime(r["post_date"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
	post_date = post_dt.astimezone(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
	slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
	chapter_file = chapters_dir / f"{post_date}-{slug}.md"
	chapter_file.write_text(content, encoding="utf-8")
	chapter_files.append(str(chapter_file))
	print(f"Wrote: {chapter_file}")

out_md.write_text("".join(parts), encoding="utf-8")
print(f"\nWrote {out_md} with {len(parts)} chapters")
print(f"Wrote {len(chapter_files)} individual files to {chapters_dir}/")

