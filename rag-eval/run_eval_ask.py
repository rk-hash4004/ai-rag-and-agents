#!/usr/bin/env python3
"""A5: end-to-end evaluation for /rag/pgvector/ask (minScore gate + Groq answer).

Reuses the same question set as run_eval.py (retrieval-only), but checks the
generation-layer behavior that run_eval.py can't: did the minScore gate make
the right grounded/ungrounded call, and does the source field match?

usage: python3 rag-eval/run_eval_ask.py [--url https://localhost:8081/rag/pgvector/ask]
"""
import argparse, json, ssl, time, urllib.request, os

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="https://localhost:8081/rag/pgvector/ask")
ap.add_argument("--file", default=os.path.join(os.path.dirname(__file__), "questions.json"))
args = ap.parse_args()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def ask(q):
    body = json.dumps({"question": q}).encode()
    req = urllib.request.Request(args.url, data=body, headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        data = json.load(r)
    return data, (time.time() - t) * 1000

questions = json.load(open(args.file))
passed, failed, lat = 0, 0, []

print(f"{'type':13} {'grounded':8} {'source ok':9} {'pass':5}  question")
for item in questions:
    expected_grounded = item["file"] is not None
    data, ms = ask(item["q"])
    lat.append(ms)

    actual_grounded = data.get("grounded")
    actual_source = data.get("source")
    grounded_ok = actual_grounded == expected_grounded
    source_ok = (actual_source == item["file"]) if expected_grounded else (actual_source is None)
    ok = grounded_ok and source_ok

    passed += ok
    failed += not ok
    print(f"{item['type']:13} {str(actual_grounded):8} {str(source_ok):9} {'PASS' if ok else 'FAIL':5}  {item['q']}")
    if not ok:
        print(f"{'':13}   expected grounded={expected_grounded} source={item['file']!r}, got grounded={actual_grounded} source={actual_source!r}")

print()
print(f"{passed}/{passed + failed} passed")
print(f"avg ask latency: {sum(lat)/len(lat):.0f} ms")
