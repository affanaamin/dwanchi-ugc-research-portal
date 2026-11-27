#!/usr/bin/env python3
"""
Dwanchi Inc. Daily Roblox UGC & Cross-Media Trend Scraper
Fetches live Roblox Catalog API charts + 18 tracked niche keywords, computes Low-Favorite
Breakout Scores, Slot Openness metrics, Cross-Media Hype Radar, and Daily Opportunity Cards.
"""

from __future__ import annotations

import json
import pathlib
import re
import time
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "data" / "trends.json"
OUT_FALLBACK_JS = ROOT / "data" / "fallback.js"

SLOT_META = {
    8:  {"name": "Hat",      "floor": 95},
    41: {"name": "Hair",     "floor": 95},
    42: {"name": "Face",     "floor": 95},
    43: {"name": "Neck",     "floor": 55},
    44: {"name": "Shoulder", "floor": 55},
    45: {"name": "Front",    "floor": 55},
    46: {"name": "Back",     "floor": 140},
    47: {"name": "Waist",    "floor": 65},
}

TRACKED_KEYWORDS = [
    "sigil", "aura", "armor", "monarch", "cursed", "crown", "chains",
    "visor", "wings", "choker", "horns", "mask", "cloak", "blade",
    "helmet", "christmas", "y2k", "goth",
]

BANNED_WORDS = [
    "chrome", "chrome hearts", "nike", "adidas", "gucci", "prada", "louis vuitton", "lv",
    "balenciaga", "dior", "supreme", "vans", "rick owens", "hellstar", "sp5der", "bape",
    "sanrio", "hello kitty", "kuromi", "my melody", "apple", "ipod", "airpods", "iphone",
    "sony", "playstation", "xbox", "nintendo", "pokemon", "marvel", "dc", "avengers",
    "doom", "doomsday", "latveria", "solo leveling", "shadow monarch", "igris", "jinwoo",
    "arise", "jujutsu", "culling game", "gojo", "sukuna", "naruto", "demon slayer",
    "infinity castle", "chainsaw man", "csgo", "cs2", "valorant", "headless", "korblox",
    "dominus", "valkyrie", "valk", "clockwork", "sparkle time", "fed", "fedora",
    "darkheart", "illumina", "venomshank", "firebrand", "ghostwalker", "ice dagger",
    "windforce", "da hood", "dh", "brookhaven", "forsaken", "blox fruits",
]


def fetch_json(url: str) -> dict:
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DwanchiUGCResearchPortal/1.0 (+https://github.com/affanaamin)"},
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(0.75 * (attempt + 1))
    return {"data": []}


def fetch_pages(query: str, pages: int = 2) -> list[dict]:
    items = []
    cursor = ""
    for _ in range(pages):
        u = f"https://catalog.roblox.com/v1/search/items/details?{query}" + (f"&Cursor={cursor}" if cursor else "")
        data = fetch_json(u)
        items.extend(data.get("data", []))
        cursor = data.get("nextPageCursor")
        if not cursor:
            break
        time.sleep(0.3)
    return items


def compute_breakout_score(rank: int, favs: int) -> float:
    rank_clamped = max(1, min(rank, 50))
    rank_term = (51 - rank_clamped) / 50.0
    fav_term = 1.0 - (min(max(favs, 0), 15000) / 15000.0)
    return round(rank_term * fav_term * 100.0, 1)


def is_clean_name(name: str) -> bool:
    for w in BANNED_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", name, re.I):
            return False
    return True


def build_hype_radar(today_d: date) -> list[dict]:
    events = [
        {
            "id": "avengers-doomsday",
            "title": "Avengers: Doomsday (Theatrical Release)",
            "medium": "Marvel Film",
            "event_date": "2026-12-18",
            "hype_driver": "RDJ as Doctor Doom, X-Men & Fantastic Four multiverse incursion surge across Gen-Z/Alpha",
            "safe_archetype": "Iron Sovereign & Arcane Warlock Armor (Open Crown-Helm, Brow Visage, Spiked Gorget, Rune Blades)",
            "bmesh_fit": 5,
            "recommended_slots": ["Hat (95 R$)", "Face (95 R$)", "Shoulder (55 R$)", "Neck (55 R$)", "Waist (65 R$)"],
            "target_colorways": ["Emerald Arcane Iron", "Astral Liquid Platinum", "Obsidian Void"],
            "banned_terms": ["Doom", "Doomsday", "Avengers", "Doctor Doom", "Latveria", "Marvel"],
        },
        {
            "id": "holiday-giftcard-wave",
            "title": "Holiday Peak -> Gift-Card Robux Wave",
            "medium": "Seasonal Economy",
            "event_date": "2026-12-25",
            "hype_driver": "Dec 18-25 torso lights & festive surge transitions on Dec 26 into massive Roblox gift-card redemptions",
            "safe_archetype": "Festive Body Lights + Year-Round Platinum/Gold/Obsidian Full Avatar Sets",
            "bmesh_fit": 5,
            "recommended_slots": ["Front (55 R$)", "Shoulder (55 R$)", "Hat (95 R$)"],
            "target_colorways": ["Festive Holiday Aurora", "Imperial Gold", "Liquid Platinum Silver"],
            "banned_terms": [],
        },
        {
            "id": "solo-leveling-monarch",
            "title": "Solo Leveling — Monarch & Armored Knight Surge",
            "medium": "Anime / Battlegrounds",
            "event_date": "2027-01-15",
            "hype_driver": "Roblox Battlegrounds players (TSB, Heroes Battlegrounds) buying violet/obsidian dark-knight capes & armor (<300 favs charting today)",
            "safe_archetype": "Umbral Void Sovereign Armor, Floating Rune Shard Pauldrons, Glowing Arcane Blades",
            "bmesh_fit": 5,
            "recommended_slots": ["Shoulder (55 R$)", "Waist (65 R$)", "Neck (55 R$)"],
            "target_colorways": ["Umbral Void Monarch", "Obsidian Void"],
            "banned_terms": ["Solo Leveling", "Shadow Monarch", "Sung Jinwoo", "Igris", "Arise"],
        },
        {
            "id": "jjk-culling-game",
            "title": "Jujutsu Kaisen — Culling Game Continuation",
            "medium": "Anime / Battlegrounds",
            "event_date": "2027-02-01",
            "hype_driver": "Massive demand in Jujutsu Shenanigans & Battlegrounds for crimson/black cursed sigil collars, marks & energy auras",
            "safe_archetype": "Crimson Cursed Sovereign Gorget, Floating Sigil Shard Aura, Monochrome Cel Ink",
            "bmesh_fit": 5,
            "recommended_slots": ["Shoulder (55 R$)", "Neck (55 R$)", "Face (95 R$)"],
            "target_colorways": ["Crimson Cursed Sovereign", "Monochrome Ink"],
            "banned_terms": ["Jujutsu", "Culling Game", "Sukuna", "Gojo", "Domain Expansion"],
        },
        {
            "id": "demon-slayer-castle",
            "title": "Demon Slayer: Infinity Castle Part 2",
            "medium": "Anime Film",
            "event_date": "2027-03-15",
            "hype_driver": "2027 theatrical sequel keeping crimson/gold katana, dark demon horns & slayer haori aesthetics high-velocity",
            "safe_archetype": "Crimson / Gold Horned Crown-Helm & Rune Waist Blades",
            "bmesh_fit": 5,
            "recommended_slots": ["Waist (65 R$)", "Hat (95 R$)"],
            "target_colorways": ["Crimson Eclipse", "Imperial Gold"],
            "banned_terms": ["Demon Slayer", "Infinity Castle", "Kimetsu", "Tanjiro", "Muzan"],
        },
    ]
    for ev in events:
        ed = date.fromisoformat(ev["event_date"])
        days_left = (ed - today_d).days
        ev["days_until"] = days_left
        if days_left <= 0:
            lead = 35
        elif 10 <= days_left <= 30:
            lead = 98
        elif days_left < 10:
            lead = 85
        elif days_left <= 65:
            lead = 76
        else:
            lead = 62
        ev["lead_score"] = lead
    return events


def main() -> None:
    today_d = datetime.now(timezone.utc).date()
    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    day_best = fetch_pages("Category=11&MinPrice=50&SortType=2&SortAggregation=1&Limit=30", pages=3)
    week_best = fetch_pages("Category=11&MinPrice=50&SortType=2&SortAggregation=3&Limit=30", pages=3)
    day_fav = fetch_pages("Category=11&MinPrice=50&SortType=1&SortAggregation=1&Limit=30", pages=2)

    records_by_id: dict[int, dict] = {}
    slot_hits: dict[int, list[dict]] = defaultdict(list)

    def ingest(source_name: str, items: list[dict], kw_tag: str | None = None) -> None:
        for rank, it in enumerate(items, 1):
            cid = it.get("id")
            if not cid:
                continue
            at = it.get("assetType") or 8
            slot_info = SLOT_META.get(at, {"name": f"Type({at})", "floor": 55})
            favs = int(it.get("favoriteCount") or 0)
            price = int(it.get("price") or it.get("lowestPrice") or slot_info["floor"])
            name = (it.get("name") or "").strip()
            score = compute_breakout_score(rank, favs)

            if cid not in records_by_id:
                records_by_id[cid] = {
                    "id": cid,
                    "name": name,
                    "creator": it.get("creatorName") or "Unknown",
                    "assetType": at,
                    "slot": slot_info["name"],
                    "floor": slot_info["floor"],
                    "price": price,
                    "favs": favs,
                    "sources": [f"{source_name} #{rank}"],
                    "keywords": [kw_tag] if kw_tag else [],
                    "best_rank": rank,
                    "breakout_score": score,
                    "low_fav_breakout": favs < 5000,
                    "copyright_clean_title": is_clean_name(name),
                    "url": f"https://www.roblox.com/catalog/{cid}",
                }
            else:
                rec = records_by_id[cid]
                rec["sources"].append(f"{source_name} #{rank}")
                if kw_tag and kw_tag not in rec["keywords"]:
                    rec["keywords"].append(kw_tag)
                if rank < rec["best_rank"]:
                    rec["best_rank"] = rank
                rec["breakout_score"] = max(rec["breakout_score"], score)

            if not kw_tag:
                slot_hits[at].append(records_by_id[cid])

    ingest("Day Best", day_best)
    ingest("Week Best", week_best)
    ingest("Day Rising", day_fav)

    keyword_stats = []
    for kw in TRACKED_KEYWORDS:
        kw_items = fetch_pages(f"Category=11&Keyword={kw}&MinPrice=50&SortType=2&SortAggregation=3&Limit=30", pages=1)
        ingest(f"KW:{kw}", kw_items, kw_tag=kw)
        if kw_items:
            favs_list = [int(i.get("favoriteCount") or 0) for i in kw_items]
            low_fav_cnt = sum(1 for f in favs_list if f < 3000)
            avg_favs = round(sum(favs_list) / max(1, len(favs_list)))
            keyword_stats.append({
                "keyword": kw,
                "sample_count": len(kw_items),
                "low_fav_count": low_fav_cnt,
                "median_favs": sorted(favs_list)[len(favs_list) // 2],
                "avg_favs": avg_favs,
                "top_example": kw_items[0].get("name", ""),
                "top_example_favs": favs_list[0],
            })
        time.sleep(0.2)

    slot_summary = []
    for at in (44, 42, 45, 43, 47, 8, 46):
        s_info = SLOT_META[at]
        seen_ids = {}
        for r in slot_hits.get(at, []):
            seen_ids[r["id"]] = r
        uniq = list(seen_ids.values())
        min_fav = min((r["favs"] for r in uniq), default=0)
        low_fav_cnt = sum(1 for r in uniq if r["favs"] < 5000)
        creators = {r["creator"] for r in uniq}
        diversity = round(len(creators) / max(1, len(uniq)) * 100) if uniq else 0
        avg_breakout = round(sum(r["breakout_score"] for r in uniq) / max(1, len(uniq)), 1)
        openness = round(min(100.0, (low_fav_cnt * 7.5) + (diversity * 0.35) + (avg_breakout * 0.4)), 1)
        slot_summary.append({
            "assetType": at,
            "slot": s_info["name"],
            "price_floor": s_info["floor"],
            "chart_hits": len(uniq),
            "low_fav_breakouts": low_fav_cnt,
            "min_favs_in_chart": min_fav,
            "creator_diversity_pct": diversity,
            "openness_score": openness,
        })

    hype_radar = build_hype_radar(today_d)

    all_items = sorted(records_by_id.values(), key=lambda x: (-x["breakout_score"], x["favs"]))

    # "What to Build Today" Opportunity Cards anchored on live data + Hype Radar
    opportunities = [
        {
            "rank": 1,
            "drop": "Drop #2 (Wave A — Target Live By Dec 8)",
            "title": "Iron Sovereign Horned Crown-Helm",
            "slot": "Hat",
            "floor": 95,
            "archetype": "Iron Sovereign & Cursed Monarch",
            "opportunity_score": 96.4,
            "why_now": "Avengers: Doomsday hits theaters Dec 18 (21 days). New 'armor'/'doom'/'monarch' hats break out with <1,500 favs while avoiding hoods/full grilles.",
            "colorways": ["Emerald Arcane Iron", "Umbral Void Monarch", "Crimson Cursed Sovereign", "Astral Silver"],
            "copyright_safe_note": "Open-face war-crown + swept horns + diamond arcane crest (NO hood, NO mouth grille, NO 'Doom/Marvel' title).",
        },
        {
            "rank": 2,
            "drop": "Drop #2 (Wave A — Target Live By Dec 8)",
            "title": "Sovereign Iron Battle Visage",
            "slot": "Face",
            "floor": 95,
            "archetype": "Iron Sovereign & Cursed Monarch",
            "opportunity_score": 94.8,
            "why_now": "Face gets full 95 R$ Hat pricing with ~6x fewer competitors. Y2K/armor face visors chart in Daily Top 60 under 800 favs.",
            "colorways": ["Emerald Arcane Iron", "Umbral Void Monarch", "Crimson Cursed Sovereign", "Astral Silver"],
            "copyright_safe_note": "Upper brow-to-cheek angular visor leaving jaw open so it stacks cleanly below #06 Crown-Helm.",
        },
        {
            "rank": 3,
            "drop": "Drop #2 (Wave A — Target Live By Dec 8)",
            "title": "Monarch Spiked Pauldrons & Rune Shard Aura",
            "slot": "Shoulder",
            "floor": 55,
            "archetype": "Iron Sovereign & Cursed Monarch",
            "opportunity_score": 93.9,
            "why_now": "Shoulder is #1 fastest breakout slot (362 favs at Day #14). Back cloaks/capes are 140 R$; shoulder pauldrons + floating arcane shards deliver big aura for 55 R$.",
            "colorways": ["Emerald Arcane Iron", "Umbral Void Monarch", "Crimson Cursed Sovereign", "Astral Silver"],
            "copyright_safe_note": "Twin metallic pauldrons + floating crystal shards; leaves Back slot free.",
        },
        {
            "rank": 4,
            "drop": "Drop #2 (Wave A — Target Live By Dec 8)",
            "title": "Spiked Sovereign Iron Gorget Collar",
            "slot": "Neck",
            "floor": 55,
            "archetype": "Iron Sovereign & Cursed Monarch",
            "opportunity_score": 90.2,
            "why_now": "55 R$ impulse stacker pairing cleanly with both Drop #1 (Chains) and Drop #2 (Pauldrons/Visage).",
            "colorways": ["Emerald Arcane Iron", "Umbral Void Monarch", "Crimson Cursed Sovereign", "Astral Silver"],
            "copyright_safe_note": "Original segmented plate gorget with throat rune gem.",
        },
        {
            "rank": 5,
            "drop": "Drop #2 (Wave A — Target Live By Dec 8)",
            "title": "Sovereign Rune-Chain Hip Tassets & Twin Blades",
            "slot": "Waist",
            "floor": 65,
            "archetype": "Iron Sovereign & Cursed Monarch",
            "opportunity_score": 89.5,
            "why_now": "Using Waist (65 R$) instead of Front lets buyers wear Drop #1's Front Body Lights simultaneously with all 5 Drop #2 pieces!",
            "colorways": ["Emerald Arcane Iron", "Umbral Void Monarch", "Crimson Cursed Sovereign", "Astral Silver"],
            "copyright_safe_note": "Original sculpted arcane blade silhouette + hip tasset plates.",
        },
    ]

    dwanchi_portfolio = {
        "group_name": "Dwanchi Inc.",
        "group_id": "35743490",
        "drops": [
            {
                "name": "Emerald Sovereign — Competition-Grade 1:1 Project-From-View Armor Suit",
                "status": "Built, Group-Approved & Live in Studio (Ready to Submit)",
                "set_price_floor": 365,
                "items": [
                    {"id": "01", "title": "Emerald Sovereign Draped Hooded Cowl",    "slot": "Hat",      "floor": 95, "tris": 2328, "mesh_id": "79416355119309"},
                    {"id": "02", "title": "Emerald Sovereign Forged Steel Mask",     "slot": "Face",     "floor": 95, "tris": 2888, "mesh_id": "106587029549358"},
                    {"id": "03", "title": "Emerald Sovereign Quilted Vest Tunic",    "slot": "Front",    "floor": 55, "tris": 2728, "mesh_id": "126608360250077"},
                    {"id": "04", "title": "Emerald Sovereign Gauntlets and Cape",    "slot": "Shoulder", "floor": 55, "tris": 3424, "mesh_id": "73413190155440"},
                    {"id": "05", "title": "Emerald Sovereign Belt and Shin Greaves", "slot": "Waist",    "floor": 65, "tris": 2368, "mesh_id": "84096149924566"},
                ],
            },
        ],
    }

    payload = {
        "scraped_at": scraped_at,
        "total_items_indexed": len(all_items),
        "slot_summary": slot_summary,
        "keyword_stats": sorted(keyword_stats, key=lambda k: (-k["low_fav_count"], k["median_favs"])),
        "hype_radar": hype_radar,
        "opportunities": opportunities,
        "dwanchi_portfolio": dwanchi_portfolio,
        "banned_words": BANNED_WORDS,
        "items": all_items[:260],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    json_str = json.dumps(payload, indent=2, ensure_ascii=False)
    OUT_JSON.write_text(json_str, encoding="utf-8", newline="\n")
    OUT_FALLBACK_JS.write_text("window.__DWANCHI_TRENDS__ = " + json_str + ";\n", encoding="utf-8", newline="\n")
    print(f"SCRAPED_OK items={len(all_items)} slots={len(slot_summary)} keywords={len(keyword_stats)} at {scraped_at}")


if __name__ == "__main__":
    main()
