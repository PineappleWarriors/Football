"""Possession pipeline: tracking -> features -> dead-ball evidence -> Viterbi spell decode.

Design: docs/council/VERDICT.md and docs/council/critiques/E-synthesis.md. numpy only, Python 3.8+.
Every constant in params.py is fixed a priori (physical or principled); nothing is fitted to the
match, its video or the ground truth.
"""
