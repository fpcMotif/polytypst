import difflib
import json
import re
from pathlib import Path

api_dir = Path("output/bench/api")
self_dir = Path("output/bench/self_hosted")

bench_pages = [10, 24, 38, 55, 75, 95, 115, 135, 155, 175]

with open(api_dir / "bench_api_meta.json") as f:
    api_meta = json.load(f)

with open(self_dir / "bench_self_hosted_meta.json") as f:
    self_meta = json.load(f)

print(f"{'Page':<6} | {'API Lat':<8} | {'Self Lat':<8} | {'API Chars':<9} | {'Self Chars':<10} | {'Similarity':<10} | {'Math Matches'}")
print("-" * 75)

total_api_lat = 0.0
total_self_lat = 0.0
sim_scores = []

math_pattern = re.compile(r"(\${1,2}[^\$]+\${1,2})")

comparison_details = []

for pno in bench_pages:
    str_pno = str(pno)
    api_info = api_meta.get(str_pno, {})
    self_info = self_meta.get(str_pno, {})

    api_text = (api_dir / f"p_{pno:03d}.md").read_text(encoding="utf-8")
    self_text = (self_dir / f"p_{pno:03d}.md").read_text(encoding="utf-8")

    api_lat = api_info.get("latency_sec", 0.0)
    self_lat = self_info.get("latency_sec", 0.0)
    total_api_lat += api_lat
    total_self_lat += self_lat

    # Similarity ratio
    matcher = difflib.SequenceMatcher(None, api_text, self_text)
    sim = matcher.ratio()
    sim_scores.append(sim)

    # Extract formulas
    api_math = set(math_pattern.findall(api_text))
    self_math = set(math_pattern.findall(self_text))
    common_math = api_math.intersection(self_math)
    all_math = api_math.union(self_math)
    math_match_pct = (len(common_math) / max(1, len(all_math))) * 100

    print(f"p_{pno:03d}  | {api_lat:5.2f}s  | {self_lat:5.2f}s  | {len(api_text):<9} | {len(self_text):<10} | {sim*100:6.2f}%   | {len(common_math)}/{len(all_math)} ({math_match_pct:.0f}%)")

    comparison_details.append({
        "page": pno,
        "api_lat": api_lat,
        "self_lat": self_lat,
        "similarity": sim,
        "api_chars": len(api_text),
        "self_chars": len(self_text),
        "api_math_count": len(api_math),
        "self_math_count": len(self_math),
        "common_math_count": len(common_math)
    })

avg_api_lat = total_api_lat / len(bench_pages)
avg_self_lat = total_self_lat / len(bench_pages)
avg_sim = sum(sim_scores) / len(sim_scores)

print("-" * 75)
print(f"Average: | {avg_api_lat:5.2f}s  | {avg_self_lat:5.2f}s  | {'':<9} | {'':<10} | {avg_sim*100:6.2f}%   |")
