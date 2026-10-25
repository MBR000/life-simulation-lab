#!/usr/bin/env python3
"""Build the reading entry points and navigation; never run an analysis.

Uses only the Python standard library. Run from any directory.
Only <!--site:*--> regions in published reports are replaced.
"""

import argparse
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
REGIONS = ("bar", "guide", "next")


def region_pattern(name):
    return re.compile(rf"<!--site:{name}-->.*?<!--/site:{name}-->", re.S)


def read(path):
    # Decode bytes directly: preserve every newline in the original reports.
    return path.read_bytes().decode("utf-8")


def load_catalog():
    catalog = json.loads(read(SITE / "reports.json"))
    reports = {item["id"]: item for item in catalog["reports"]}
    if len(reports) != len(catalog["reports"]):
        raise ValueError("Duplicate report ID")
    groups = catalog["groups"]
    if len({g["id"] for g in groups}) != len(groups):
        raise ValueError("Duplicate group ID")
    if not groups or groups[0]["id"] != "main" or not groups[0]["reports"]:
        raise ValueError("The first group must be a non-empty main reading path")
    assigned = [ident for group in groups for ident in group["reports"]]
    if len(set(assigned)) != len(assigned) or set(assigned) != set(reports):
        raise ValueError("Each report must belong to exactly one group")
    files = [r["file"] for r in reports.values()]
    if len(set(files)) != len(files):
        raise ValueError("Duplicate report filename")
    for group in groups:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", group["id"]):
            raise ValueError(f"Invalid group ID: {group['id']}")
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", group["color"]):
            raise ValueError(f"Invalid group color: {group['id']}")
    for report in reports.values():
        filename = report["file"]
        if Path(filename).name != filename or not filename.endswith(".html"):
            raise ValueError(f"Expected root-level HTML report: {filename}")
        content = read(ROOT / filename)
        for name in REGIONS:
            if (content.count(f"<!--site:{name}-->") != 1
                    or content.count(f"<!--/site:{name}-->") != 1
                    or len(region_pattern(name).findall(content)) != 1):
                raise ValueError(f"{filename}: expected one site:{name} region")
        for link in report["links"]:
            href = link["href"]
            if not href.startswith("#") or not re.search(
                rf'\bid=[\"\']{re.escape(href[1:])}[\"\']', content
            ):
                raise ValueError(f"{filename}: missing local anchor {href}")
    return groups, reports


def a(href, label, cls=""):
    attr = f' class="{escape(cls)}"' if cls else ""
    return f'<a{attr} href="{escape(href)}">{escape(label)}</a>'


def render_template(filename, values):
    template = read(SITE / filename)
    def replace(match):
        key = match.group(1)
        if key not in values:
            raise ValueError(f"{filename}: unknown placeholder {key}")
        return values[key]
    return re.sub(r"\{\{([A-Z_]+)\}\}", replace, template)


def navigation(report, group, reports, main):
    is_main = group["id"] == "main"
    position = group["reports"].index(report["id"])
    if is_main:
        context = f"主线 {position + 1} / {len(main)}"
        home = "index.html#main"
    else:
        context = "专题 · " + group["title"]
        home = "reports.html#" + group["id"]
    bar = (
        '<nav class="site-bar" aria-label="站点导航">'
        + a("index.html", "人生模拟实验室", "brand")
        + a(home, context, "chap")
        + f'<span class="crumb">{escape(report["label"])}</span>'
        + '<span class="nx">' + a("reports.html", "全部报告") + '</span></nav>'
    )
    links = " ".join(a(link["href"], link["label"]) for link in report["links"])
    guide = (
        '<aside class="site-guide" aria-label="阅读提示">'
        + f'<p class="route-context">{escape(report["role"])}</p>'
        + '<details><summary>阅读提示与页内导航</summary>'
        + f'<p>{escape(report["caution"])}</p>'
        + f'<div class="read">{links}</div></details></aside>'
    )
    if is_main:
        previous = reports[main[position - 1]] if position else None
        following = reports[main[position + 1]] if position + 1 < len(main) else None
        left = footer_link(previous["file"], "← 主线上一篇", previous["title"]) if previous else footer_link("index.html#main", "阅读路线", "回到主线首页")
        right = footer_link(following["file"], "主线下一篇 →", following["title"], "r") if following else footer_link("reports.html", "主线读完了", "按问题选择一篇专题 →", "r")
    else:
        left = footer_link("index.html#main", "回到主线", "起点 → 策略 → 一次选择")
        right = footer_link(home, "继续探索", group["title"] + "专题 →", "r")
    bottom = (
        '<nav class="site-next" aria-label="继续阅读">' + left + right
        + a("reports.html", "全部报告与方法说明", "home") + '</nav>'
    )
    return {"bar": bar, "guide": guide, "next": bottom}


def footer_link(href, eyebrow, title, cls=""):
    return (f'<a class="{cls}" href="{escape(href)}">'
            f'<small>{escape(eyebrow)}</small><b>{escape(title)}</b></a>')


def build_outputs(groups, reports):
    main = groups[0]["reports"]
    main_rows = []
    # Preserve the old homepage's useful fragment destinations.
    legacy = {"A_peers2002": "base", "B_country": "origin", "C_strategy": "choice"}
    for number, ident in enumerate(main, 1):
        report = reports[ident]
        anchor = f' id="{legacy[ident]}"' if ident in legacy else ""
        main_rows.append(
            f'<li{anchor}><a class="path-row" href="{escape(report["file"])}">'
            f'<span class="step">{number:02d}</span><div>'
            f'<span class="eyebrow">{escape(report["label"])}</span>'
            f'<h3>{escape(report["title"])}</h3><p>{escape(report["role"])}</p>'
            f'</div><span class="arrow" aria-hidden="true">↗</span></a></li>'
        )
    topic_cards = []
    catalog_groups = []
    for group in groups:
        if group["id"] != "main":
            topic_cards.append(
                f'<a class="topic-card" href="reports.html#{group["id"]}" style="--topic:{group["color"]}">'
                f'<span class="eyebrow">{len(group["reports"])} 篇专题</span>'
                f'<h3>{escape(group["title"])} <span aria-hidden="true">↗</span></h3>'
                f'<p>{escape(group["description"])}</p></a>'
            )
        rows = []
        for ident in group["reports"]:
            report = reports[ident]
            rows.append(
                f'<li><a href="{escape(report["file"])}"><span class="report-id">{escape(ident)}</span>'
                f'<div><h3>{escape(report["title"])}</h3><p>{escape(report["question"])}</p></div>'
                '<span class="arrow" aria-hidden="true">↗</span></a></li>'
            )
        catalog_groups.append(
            f'<section class="catalog-group" id="{group["id"]}" style="--topic:{group["color"]}">'
            f'<div class="group-heading"><h2>{escape(group["title"])}</h2><p>{escape(group["description"])}</p></div>'
            '<ul class="report-list">' + "\n".join(rows) + '</ul></section>'
        )
    values = {
        "MAIN_ROWS": "\n".join(main_rows),
        "TOPIC_CARDS": "\n".join(topic_cards),
        "CATALOG_GROUPS": "\n".join(catalog_groups),
        "GROUP_LINKS": "\n".join(a("#" + g["id"], g["title"]) for g in groups),
        "MAIN_COUNT": str(len(main)),
        "TOPIC_COUNT": str(len(reports) - len(main)),
        "REPORT_COUNT": str(len(reports)),
        "FIRST_REPORT": escape(reports[main[0]]["file"]),
        "OVERVIEW": read(SITE / "overview.fragment.html"),
    }
    outputs = {ROOT / "index.html": render_template("index.template.html", values),
               ROOT / "reports.html": render_template("reports.template.html", values)}
    for group in groups:
        for ident in group["reports"]:
            report = reports[ident]
            path = ROOT / report["file"]
            content = read(path)
            for name, body in navigation(report, group, reports, main).items():
                replacement = f"<!--site:{name}-->{body}<!--/site:{name}-->"
                content = region_pattern(name).sub(lambda _: replacement, content)
            outputs[path] = content
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated pages are out of date; do not write files")
    args = parser.parse_args()
    try:
        groups, reports = load_catalog()
        # Compute and validate everything before changing any file.
        outputs = build_outputs(groups, reports)
        stale = [path for path, content in outputs.items()
                 if not path.exists() or read(path) != content]
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Site build failed: {error}\n")
    if args.check:
        if stale:
            print("Out of date: " + ", ".join(path.name for path in stale))
            return 1
        print(f"OK: {len(outputs)} pages match the catalog and templates.")
        return 0
    for path in stale:
        path.write_bytes(outputs[path].encode("utf-8"))
    print(f"Updated {len(stale)} of {len(outputs)} pages; report analysis and data were not regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
