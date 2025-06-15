import streamlit as st
import itertools
from collections import Counter

st.set_page_config(page_title="DC-5 Guided Combo Generator", layout="wide")
st.title("🎯 DC-5 Combo Generator by Filter Rules Only")

st.markdown("This tool generates 5-digit combinations based only on filter rules, **not** by enumerating the full 00000–99999 space.")

# --- Input: Hot, Cold, Due, Seed Digits ---
hot = st.text_input("Enter hot digits (comma-separated):")
cold = st.text_input("Enter cold digits (comma-separated):")
due = st.text_input("Enter due digits (comma-separated):")
seed = st.text_input("Enter seed digits (comma-separated):")

if all([hot, cold, due, seed]):
    hot_digits = set(hot.split(","))
    cold_digits = set(cold.split(","))
    due_digits = set(due.split(","))
    seed_digits = set(seed.split(","))

    # --- Most Frequent Target Sums ---
    top_sums = {13, 14, 17, 19, 21, 23, 24, 26, 28, 30}

    candidates = []
    all_digits = list(set(hot_digits | cold_digits | due_digits | seed_digits))

    # Generate all possible 5-digit combinations from these digits (with repeat)
    for combo in itertools.product(all_digits, repeat=5):
        digits = list(combo)

        # --- Rule: At least 2 seed digits ---
        if sum(d in seed_digits for d in digits) < 2:
            continue

        # --- Rule: At least 2 from hot/cold/due pool combined ---
        if sum(d in (hot_digits | cold_digits | due_digits) for d in digits) < 2:
            continue

        # --- Rule: No triple or higher repetition ---
        if max(Counter(digits).values()) >= 3:
            continue

        # --- Rule: Mirror Sum ≠ Digit Sum ---
        if sum(map(int, digits)) == sum([9 - int(d) for d in digits]):
            continue

        # --- Rule: All digits not from same V-Trac group ---
        if len(set(int(d)%5 for d in digits)) == 1:
            continue

        # --- Rule: Prime Digit Filter (3+ unique primes is bad) ---
        prime_digits = {"2", "3", "5", "7"}
        if len(set(d for d in digits if d in prime_digits)) >= 3:
            continue

        # --- Rule: No more than 1 digit ≥ 8 ---
        if sum(1 for d in digits if int(d) >= 8) >= 2:
            continue

        # --- Rule: Sum not ending in 0 or 5 ---
        if sum(map(int, digits)) % 10 in {0, 5}:
            continue

        # --- Rule: Must match top frequent target sums ---
        if sum(map(int, digits)) not in top_sums:
            continue

        # Passed all rules
        candidates.append("".join(digits))

    # Deduplicate by sorted box form
    seen = set()
    deduped = []
    for c in candidates:
        box = "".join(sorted(c))
        if box not in seen:
            seen.add(box)
            deduped.append(c)

    st.success(f"Generated {len(deduped)} unique box combinations that match all filters ✅")

    for c in deduped:
        st.write(c)

    st.download_button(
        "Download Combos",
        data="\n".join(deduped),
        file_name="filtered_combos.txt",
        mime="text/plain"
    )
