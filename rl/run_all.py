"""One entry point: data -> fold A -> fold B -> final model -> report. Resumable.

    python -m rl.run_all --hours 8          (use --smoke for a ~6-minute check)
"""
import argparse
import json
import os
import sys
import time
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.simplefilter("ignore", RuntimeWarning)

from rl import data  # noqa: E402


def dead_model_for(game_name):
    from train_dead_model import collect          # experiments/ is on sys.path via rl.data
    from possession import ml
    X, y = collect(game_name)
    k = y < 3
    return ml.fit_logistic(X[k], (y[k] == 2).astype(float), l2=1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=8.0)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(ROOT, "rl", "runs", "latest"))
    args = ap.parse_args()
    minutes = 5.0 if args.smoke else args.hours * 60.0
    eval_every = 10 if args.smoke else 100
    os.makedirs(args.out, exist_ok=True)

    from rl import train
    fh = open(os.path.join(args.out, "log.txt"), "a")
    train.log(fh, "start: budget {:.0f} min, smoke={}".format(minutes, args.smoke))

    train.log(fh, "step 1/5: data")
    data.ensure_data()
    g1, g2 = (data.build_game(g) for g in data.GAMES)
    games = {data.GAMES[0]: g1, data.GAMES[1]: g2}

    folds = [("A_train1_val2", data.GAMES[0], data.GAMES[1]),
             ("B_train2_val1", data.GAMES[1], data.GAMES[0])]
    results = {}
    t_fold = minutes * 0.4
    for tag, tr, va in folds:
        res_path = os.path.join(args.out, tag + ".json")
        if os.path.exists(res_path):
            results[tag] = json.load(open(res_path))
            train.log(fh, "fold {} already done, skipping".format(tag))
            continue
        train.log(fh, "step: fold {} (train {}, validate {}) for {:.0f} min".format(
            tag, tr, va, t_fold))
        fdir = os.path.join(args.out, tag)
        os.makedirs(fdir, exist_ok=True)
        dm = dead_model_for(tr)                         # comparator: Viterbi model, trained on tr
        vit = train.viterbi_scores(games[va], dm)
        train.log(fh, "Viterbi comparator on {}: period1 spell {:.3f} macro {:.3f} | period2 spell "
                      "{:.3f} macro {:.3f}".format(va, *vit[1], *vit[2]))
        state, _, _ = train.train_policy([games[tr]], games[va], fdir, t_fold, args.seed, fh,
                                         eval_every=eval_every, smoke=args.smoke)
        hist = state["history"]
        rl_hist = [h for h in hist if h["phase"] == "rl"]
        best = next((h for h in rl_hist if h["it"] == state["best_it"]), rl_hist[-1] if rl_hist else None)
        imit = [h for h in hist if h["phase"] == "imit"]
        results[tag] = {"viterbi_report": vit[2], "viterbi_select": vit[1],
                        "imitation_report": [imit[-1]["rep_spell"], imit[-1]["rep_macro"]] if imit else None,
                        "rl_best": best, "rl_last": rl_hist[-1] if rl_hist else None,
                        "best_it": state["best_it"]}
        json.dump(results[tag], open(res_path, "w"), indent=1)

    train.log(fh, "step 4/5: final model on both games")
    final_dir = os.path.join(args.out, "final")
    os.makedirs(final_dir, exist_ok=True)
    iters = [r["best_it"] for r in results.values() if r.get("best_it")]
    fixed = int(sorted(iters)[len(iters) // 2]) if iters else None
    train.train_policy([g1, g2], None, final_dir, minutes * 0.2, args.seed, fh,
                       eval_every=10 ** 9, smoke=args.smoke, fixed_iters=fixed)

    train.log(fh, "step 5/5: report")
    lines = ["# RL vs Viterbi (external games only)", "",
             "Reported number = held-out game, period 2 (checkpoint selected on period 1).", "",
             "| fold | Viterbi | imitation only | RL best-selected | RL last |", "|---|---|---|---|---|"]
    gains = []
    for tag, r in results.items():
        f = lambda v: "-" if not v else "{:.3f} / {:.3f}".format(*v)
        b = r["rl_best"]
        lines.append("| {} | {} | {} | {} | {} |".format(
            tag, f(r["viterbi_report"]), f(r["imitation_report"]),
            f([b["rep_spell"], b["rep_macro"]]) if b else "-",
            f([r["rl_last"]["rep_spell"], r["rl_last"]["rep_macro"]]) if r["rl_last"] else "-"))
        if b:
            gains.append(b["rep_spell"] - r["viterbi_report"][0])
    verdict = ("RL beat Viterbi on spellF1 in both folds by >0.02: promising, validate further."
               if gains and min(gains) > 0.02 else
               "No convincing evidence that RL beats the Viterbi model (needs > +0.02 spellF1 in both folds). "
               "Keep Viterbi.")
    lines += ["", "(spellF1 / macroF1)", "", "**Verdict:** " + verdict]
    open(os.path.join(args.out, "report.md"), "w").write("\n".join(lines))
    train.log(fh, "DONE. Read " + os.path.join(args.out, "report.md"))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
