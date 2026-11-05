"""Align the (unsynchronised) broadcast tracking to the tactical timeline, algorithmically.

Signal: per-frame 'team of the player nearest the ball' (-1 = no ball) computed the same way for
both feeds (tactical side = organiser baseline_raw.csv; broadcast side = same rule on broadcast ATD).
1. Slide 60 s broadcast windows over the tactical series with FFT cross-correlation (sum of signed
   agreements); keep confident peaks (agreement >= 0.8, overlap >= 500, clear of runner-up).
2. Cluster the confident lags (tactical = broadcast + lag): each cluster with >= 3 windows is a lag.
3. Verify every 10 s broadcast window against each lag (+-3 frame refinement) and keep it only if
   its agreement is >= 0.75 and >= 0.15 above shifted-lag controls (replays/other cameras fail).
No ground truth, video or manual input is used.
"""
import numpy as np


def _signed(c):
    return (np.where(c == 0, 1.0, np.where(c == 1, -1.0, 0.0)).astype(np.float32),
            (c >= 0).astype(np.float32))


def find_lags(b, t, win=1500, min_overlap=500, min_windows=3):
    sb, mb = _signed(b)
    st, mt = _signed(t)
    n = 1 << int(np.ceil(np.log2(len(t) + win)))
    fs, fm = np.fft.rfft(st, n), np.fft.rfft(mt, n)

    def corr(x, f):
        return np.fft.irfft(np.conj(np.fft.rfft(x, n)) * f, n)[:len(t)]

    lags = []
    for a in range(0, len(b) - win, win // 2):
        num, den = corr(sb[a:a + win], fs), corr(mb[a:a + win], fm)
        sc = np.where(den >= 200, num, -1e9)
        j = int(np.argmax(sc))
        s2 = sc.copy()
        s2[max(0, j - 100):j + 100] = -1e9
        if den[j] >= min_overlap and num[j] / den[j] >= 0.8 and num[j] > 1.15 * max(s2.max(), 1):
            lags.append(j - a)
    lags = np.array(sorted(lags))
    out, i = [], 0
    while i < len(lags):
        grp = lags[(lags >= lags[i]) & (lags <= lags[i] + 5)]
        if len(grp) >= min_windows:
            out.append(int(np.median(grp)))
        i += len(grp)
    return out


def _agree(b, t, bs, be, lag):
    ts, te = bs + lag, be + lag
    if ts < 0 or te > len(t):
        return np.nan
    x, y = b[bs:be], t[ts:te]
    m = (x >= 0) & (y >= 0)
    return float((x[m] == y[m]).mean()) if m.sum() >= 60 else np.nan


def build_source_map(b, t, lags, win=250, min_agree=0.75, margin=0.15):
    """src[tactical_frame] = broadcast frame (or -1) for verified live-feed windows."""
    src = np.full(len(t), -1, dtype=np.int64)
    for a in range(0, len(b) - win, win // 2):
        best = None
        for lag in lags:
            for d in range(-3, 4):
                s = _agree(b, t, a, a + win, lag + d)
                if not np.isnan(s) and (best is None or s > best[0]):
                    best = (s, lag + d)
        if best is None or best[0] < min_agree:
            continue
        ctrl = [_agree(b, t, a, a + win, best[1] + o) for o in (-4000, -2500, 2500, 4000)]
        ctrl = [c for c in ctrl if not np.isnan(c)]
        if ctrl and best[0] - float(np.median(ctrl)) >= margin:
            for f in range(a, a + win // 2):
                if 0 <= f + best[1] < len(t):
                    src[f + best[1]] = f
    return src
