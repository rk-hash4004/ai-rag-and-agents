#!/usr/bin/env python3
"""Retrieval evaluation for /rag/search (no LLM calls).

usage: python3 rag-eval/run_eval.py [--k 5] [--url https://localhost:8081/rag/search]
For each question, finds the rank of the expected chunk (file + section heading).
Reports hit@1, hit@3, hit@K, and how well a minScore threshold could separate
in-scope questions from out-of-scope ones.
"""
import argparse, json, ssl, time, urllib.request, os

ap = argparse.ArgumentParser()
ap.add_argument("--k", type=int, default=5)
ap.add_argument("--url", default="https://localhost:8081/rag/search")
ap.add_argument("--file", default=os.path.join(os.path.dirname(__file__), "questions.json"))
args = ap.parse_args()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def search(q):
    body = json.dumps({"question": q, "maxResults": args.k}).encode()
    req = urllib.request.Request(args.url, data=body, headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        data = json.load(r)
    return data["retrievedChunks"], (time.time() - t) * 1000

questions = json.load(open(args.file))
rows, in_scope_scores, oos_tops, lat = [], [], [], []
hit = {1: 0, 3: 0, args.k: 0}
n_in = 0

print(f"{'type':13} {'rank':>4} {'top':>6} {'right':>6}  question")
for item in questions:
    chunks, ms = search(item["q"])
    lat.append(ms)
    top = chunks[0]["score"] if chunks else 0
    if item["file"] is None:
        oos_tops.append(top)
        print(f"{item['type']:13} {'-':>4} {top:6.3f} {'-':>6}  {item['q']}")
        continue
    n_in += 1
    rank, right = None, None
    for i, c in enumerate(chunks, 1):
        if c["source"] == item["file"] and item["section"] in c["text"]:
            rank, right = i, c["score"]
            break
    if rank:
        in_scope_scores.append(right)
        for k in hit:
            if rank <= k:
                hit[k] += 1
    print(f"{item['type']:13} {str(rank or 'miss'):>4} {top:6.3f} {(right or 0):6.3f}  {item['q']}")

print()
print(f"in-scope questions: {n_in}   out-of-scope: {len(oos_tops)}   K={args.k}")
for k in sorted(hit):
    print(f"hit@{k}: {hit[k]}/{n_in} = {hit[k]/n_in:.0%}")
print(f"avg search latency: {sum(lat)/len(lat):.0f} ms")
if in_scope_scores and oos_tops:
    lo, hi = min(in_scope_scores), max(oos_tops)
    print(f"lowest score of a RIGHT chunk : {lo:.3f}")
    print(f"highest top score out-of-scope: {hi:.3f}")
    if lo > hi:
        print(f"a minScore between {hi:.3f} and {lo:.3f} separates them")
    else:
        print("scores OVERLAP: no single minScore separates in-scope from out-of-scope")
