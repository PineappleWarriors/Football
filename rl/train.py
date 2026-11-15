"""Imitation pre-training then policy-gradient RL on spellF1 (+macroF1), with cross-game validation.

Within the held-out game: period 1 selects the checkpoint, period 2 is the reported score (so the
reported number is not selected on). Everything is external-game data only.
"""
import json
import os
import threading
import time

import numpy as np
import torch
import torch.nn.functional as F

from rl.data import E, ROOT  # noqa: F401  (also sets sys.path)
import possession_metrics as pm  # noqa: E402
from possession.model import decode_period  # noqa: E402
from possession import external_metrica as em  # noqa: E402
from rl.policy import Policy  # noqa: E402

STOP = threading.Event()      # set by Ctrl+C handler: finish the step, save, exit
W = 1500          # window = 5 min at 5 Hz
K = 8             # sampled label sequences per window
B = 4             # windows per RL step


def log(fh, msg):
    line = "[{}] {}".format(time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    fh.write(line + "\n")
    fh.flush()


class Norm:
    def __init__(self, games):
        X = np.concatenate([p["X"] for g in games for p in g["periods"].values()])
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-6

    def __call__(self, X):
        return ((X - self.mu) / self.sd).astype(np.float32)


class Windows:
    def __init__(self, games, norm, rng):
        self.items = []
        for g in games:
            for p in g["periods"].values():
                bad = np.concatenate(([0], np.cumsum(p["y"] == 3)))
                starts = [s for s in range(0, len(p["y"]) - W, 50) if bad[s + W] - bad[s] == 0]
                if starts:
                    self.items.append((norm(p["X"]), p["y"], np.array(starts)))
        self.rng = rng

    def batch(self, n):
        xs, ys = [], []
        for _ in range(n):
            X, y, starts = self.items[self.rng.randint(len(self.items))]
            s = starts[self.rng.randint(len(starts))]
            xs.append(X[s:s + W])
            ys.append(y[s:s + W])
        return torch.from_numpy(np.stack(xs)), torch.from_numpy(np.stack(ys))


def reward(gt, pred):
    """spellF1 (mean over IoUs) + 0.5*macroF1 on a 5 Hz window with no X."""
    runs = [(0, len(gt))]
    sp = pm.spell_scores(gt.astype(np.int8), pred.astype(np.int8), runs)["mean_f1"]
    mf = pm.macro_f1(pm.scored_confusion(pm.confusion(gt.astype(np.int8), pred.astype(np.int8))))
    return sp + 0.5 * mf


def period_pred25(game, period, path):
    """5 Hz path of one period -> 25 Hz codes array (3 outside that period)."""
    d, n = game["raw"], game["n"]
    out = np.full(n, 3, dtype=np.int8)
    fr = game["periods"][period]["frame"]
    lo, hi = fr[0], min(fr[-1] + 5, n)
    pos = np.clip(np.rint(np.arange(lo, hi) / 5.0).astype(int) - int(round(fr[0] / 5.0)),
                  0, len(path) - 1)
    out[lo:hi] = path[pos]
    return out


def score_period(game, period, path):
    pred = period_pred25(game, period, path)
    gt = np.where(pred == 3, 3, game["gt25"]).astype(np.int8)
    r = E.score({"gt": gt}, pred)
    return r["spellF1"], r["macroF1"]


@torch.no_grad()
def greedy_path(policy, norm, game, period, device):
    policy.eval()
    X = torch.from_numpy(norm(game["periods"][period]["X"]))[None].to(device)
    path = policy(X)[0].argmax(-1).cpu().numpy()
    policy.train()
    return path


def viterbi_paths(game, dead_model):
    paths = {}
    for p in game["periods"]:
        m = game["raw"]["period"] == p
        trk = {k: game["raw"][k][m] for k in ("players", "pspeed", "ball")}
        trk["team"] = game["raw"]["team"]
        paths[p] = decode_period(trk, em.PITCH, dead_model)
    return paths


def viterbi_scores(game, dead_model):
    out = {}
    for p in game["periods"]:
        m = game["raw"]["period"] == p
        trk = {k: game["raw"][k][m] for k in ("players", "pspeed", "ball")}
        trk["team"] = game["raw"]["team"]
        out[p] = score_period(game, p, decode_period(trk, em.PITCH, dead_model))
    return out


def train_policy(train_games, val_game, out_dir, minutes, seed, fh, dead_model=None,
                 imit_frac=0.15, eval_every=100, temp=0.5, lr_rl=1e-4, ce_coef=0.3, ent_coef=0.01,
                 smoke=False, fixed_iters=None, rec=None, stage="stage", vit_paths=None,
                 vit_score=None):
    rng = np.random.RandomState(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    norm = Norm(train_games)
    wins = Windows(train_games, norm, rng)
    n_feat = train_games[0]["periods"][1]["X"].shape[1]
    policy = Policy(n_feat).to(device)
    ck = os.path.join(out_dir, "checkpoint.pt")
    state = {"phase": "imit", "it": 0, "best": -1.0, "best_it": 0, "history": [], "elapsed": 0.0}
    opt = torch.optim.Adam(policy.parameters(), lr=1e-3)
    if os.path.exists(ck):
        blob = torch.load(ck, map_location=device, weights_only=False)
        policy.load_state_dict(blob["policy"])
        opt.load_state_dict(blob["opt"])
        state = blob["state"]
        log(fh, "resumed from checkpoint at it={} phase={}".format(state["it"], state["phase"]))
    state.setdefault("elapsed", 0.0)
    base, t0 = state["elapsed"], time.time()
    budget = 60.0 * minutes

    def elapsed():
        return base + (time.time() - t0)

    def tick():
        state["elapsed"] = elapsed()
        if rec:
            rec.update(stage, state, budget)

    sel_p, rep_p = (1, 2) if val_game else (None, None)
    demo = None
    if val_game and rec:
        n5 = len(val_game["periods"][rep_p]["y"])
        a0 = min(n5 // 3, max(0, n5 - W))
        demo = (a0, min(n5, a0 + W))
        letters = "HADX"
        yv = val_game["periods"][rep_p]["y"][demo[0]:demo[1]]
        rec.set_reference(stage, "".join(letters[int(v)] for v in yv),
                          "".join(letters[int(v)] for v in vit_paths[rep_p][demo[0]:demo[1]])
                          if vit_paths else None, vit_score)

    def evaluate(tag):
        if not val_game:
            return None
        a = score_period(val_game, sel_p, greedy_path(policy, norm, val_game, sel_p, device))
        b = score_period(val_game, rep_p, greedy_path(policy, norm, val_game, rep_p, device))
        sel = a[0] + 0.5 * a[1]
        entry = {"it": state["it"], "phase": state["phase"], "sel_spell": a[0], "sel_macro": a[1],
                 "rep_spell": b[0], "rep_macro": b[1]}
        state["history"].append(entry)
        log(fh, "{} it={} select(p{}): spell {:.3f} macro {:.3f} | report(p{}): spell {:.3f} "
                "macro {:.3f}".format(tag, state["it"], sel_p, a[0], a[1], rep_p, b[0], b[1]))
        if rec and demo is not None:
            with torch.no_grad():
                policy.eval()
                Xv = torch.from_numpy(norm(val_game["periods"][rep_p]["X"]))[None].to(device)
                pr = torch.softmax(policy(Xv)[0], -1).cpu().numpy()
                policy.train()
            seg = pr[demo[0]:demo[1]]
            rec.snapshot(stage, state["it"], state["phase"],
                         "".join("HAD"[int(v)] for v in seg.argmax(-1)),
                         [round(float(v), 2) for v in seg.max(-1)[::5]], entry)
        elif rec:
            rec.snapshot(stage, state["it"], state["phase"], None, None, entry)
        if state["phase"] == "rl" and sel > state["best"]:
            state["best"], state["best_it"] = sel, state["it"]
            torch.save({"policy": policy.state_dict(), "norm": (norm.mu, norm.sd)},
                       os.path.join(out_dir, "best.pt"))
        return entry

    def save():
        torch.save({"policy": policy.state_dict(), "opt": opt.state_dict(), "state": state}, ck)

    # ---- phase 1: imitation (cross-entropy on event-derived labels)
    while state["phase"] == "imit" and elapsed() < budget * imit_frac and not STOP.is_set():
        x, y = wins.batch(8)
        loss = F.cross_entropy(policy(x.to(device)).reshape(-1, 3), y.to(device).reshape(-1),
                               ignore_index=3)
        opt.zero_grad(); loss.backward(); opt.step()
        state["it"] += 1
        if state["it"] % 50 == 0:
            log(fh, "imit it={} loss {:.4f}".format(state["it"], float(loss)))
        if rec:
            rec.metric(stage, "imit_loss", state["it"], float(loss))
        if state["it"] % 10 == 0:
            tick()
        if state["it"] % eval_every == 0:
            evaluate("imit")
            save()
    if state["phase"] == "imit" and not STOP.is_set():
        state["phase"], state["it"] = "rl", 0
        for g in opt.param_groups:
            g["lr"] = lr_rl
        evaluate("imit-final")
        torch.save({"policy": policy.state_dict(), "norm": (norm.mu, norm.sd)},
                   os.path.join(out_dir, "imitation.pt"))
        save()

    # ---- phase 2: REINFORCE on the metric, anchored to the labels
    while (state["phase"] == "rl" and elapsed() < budget and not STOP.is_set()
           and (fixed_iters is None or state["it"] < fixed_iters)):
        x, y = wins.batch(B)
        x, y = x.to(device), y.to(device)
        logits = policy(x)
        dist = torch.distributions.Categorical(logits=logits / temp)
        acts = dist.sample((K,))                                  # [K,B,W]
        a_np, y_np = acts.cpu().numpy(), y.cpu().numpy()
        R = np.array([[reward(y_np[b], a_np[k, b]) for b in range(B)] for k in range(K)])
        adv = (R - R.mean(0, keepdims=True)) / (R.std(0, keepdims=True) + 1e-6)
        logp = dist.log_prob(acts)
        adv_t = torch.from_numpy(adv).float().to(device)[..., None]    # [K,B,1]
        pg = -(adv_t * logp).mean()
        ce = F.cross_entropy(logits.reshape(-1, 3), y.reshape(-1), ignore_index=3)
        loss = pg - ent_coef * dist.entropy().mean() + ce_coef * ce
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
        opt.step()
        state["it"] += 1
        if rec:
            rec.metric(stage, "reward", state["it"], float(R.mean()))
            rec.metric(stage, "ce", state["it"], float(ce))
            rec.metric(stage, "entropy", state["it"], float(dist.entropy().mean()))
        if state["it"] % 5 == 0:
            tick()
        if state["it"] % 20 == 0:
            log(fh, "rl it={} mean reward {:.3f} ce {:.3f}".format(state["it"], R.mean(), float(ce)))
        if state["it"] % eval_every == 0:
            evaluate("rl")
            save()
    if state["phase"] == "rl":
        evaluate("stopped" if STOP.is_set() else "final")
    tick()
    torch.save({"policy": policy.state_dict(), "norm": (norm.mu, norm.sd)},
               os.path.join(out_dir, "last.pt"))
    save()
    state["finished"] = (not STOP.is_set()) and state["phase"] == "rl"
    return state, policy, norm
