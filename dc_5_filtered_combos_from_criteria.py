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

# --- Toggles for filters ---
run_filters = st.checkbox("✅ Apply all filters (recommended)", value=False)
exclude_triples = st.checkbox("Eliminate Triples (3 of the same digit)", value=False)
apply_spread_filter = st.checkbox("Filter: Digit Spread < 4", value=False)
apply_mirror_filter = st.checkbox("Filter: Mirror Count < 2", value=False)
apply_high_digit_filter = st.checkbox("Filter: Max 2 digits > 5", value=False)
apply_vtrac_filter = st.checkbox("Filter: No 4+ repeats of same V-Trac group", value=False)
apply_prime_filter = st.checkbox("Filter: 3+ Unique Prime Digits", value=False)
apply_sum_trap_filter = st.checkbox("Filter: Sum ends in 0 or 5", value=False)
apply_mirror_sum_filter = st.checkbox("Filter: Mirror Sum = Digit Sum", value=False)
apply_uniform_vtrac_filter = st.checkbox("Filter: All digits same V-Trac group", value=False)
apply_top_sum_filter = st.checkbox("Filter: Must match top 10 frequent sums", value=False)

save_preset = st.checkbox("Save current filter settings")

if all([hot, cold, due, seed]):
    hot_digits = set(hot.split(","))
    cold_digits = set(cold.split(","))
    due_digits = set(due.split(","))
    seed_digits = set(seed.split(","))

    # --- Top Frequent Target Sums (non-optional percentile filter) ---
    top_sums = {13, 14, 17, 19, 21, 23, 24, 26, 28, 30}

    candidates = []
    all_digits = list(set(hot_digits | cold_digits | due_digits | seed_digits))

    st.write(f"Initial combos before filtering: {len(all_digits) ** 5}")

    for combo in itertools.product(all_digits, repeat=5):
        digits = list(combo)
        digit_counts = Counter(digits)

        # --- Core Rule: Must match top frequent sums ---
        digit_sum = sum(map(int, digits))
        if digit_sum not in top_sums:
            continue

        if not run_filters:
            candidates.append("".join(digits))
            continue

        # --- Required Conditions ---
        if sum(d in seed_digits for d in digits) < 2:
            continue
        if sum(d in (hot_digits | cold_digits | due_digits) for d in digits) < 2:
            continue
        if max(digit_counts.values()) >= 4:
            continue  # Eliminate quads and quints
        if exclude_triples and max(digit_counts.values()) >= 3:
            continue

        # --- Optional Filters ---
        if apply_mirror_sum_filter and sum(map(int, digits)) == sum([9 - int(d) for d in digits]):
            continue
        if apply_uniform_vtrac_filter and len(set(int(d)%5 for d in digits)) == 1:
            continue
        if apply_prime_filter and len(set(d for d in digits if d in {"2", "3", "5", "7"})) >= 3:
            continue
        if apply_high_digit_filter and sum(1 for d in digits if int(d) >= 8) >= 2:
            continue
        if apply_sum_trap_filter and digit_sum % 10 in {0, 5}:
            continue
        if apply_spread_filter and (max(map(int, digits)) - min(map(int, digits))) < 4:
            continue
        if apply_mirror_filter and sum(d in {"0","1","2","3","4","5","6","7","8","9"} for d in digits) < 2:
            continue
        if apply_vtrac_filter and max(Counter([int(d)%5 for d in digits]).values()) >= 4:
            continue

        candidates.append("".join(digits))

    st.write(f"After filtering: {len(candidates)} combos remain")

    # --- Deduplicate by box form
    seen = set()
    deduped = []
    for c in candidates:
        box = "".join(sorted(c))
        if box not in seen:
            seen.add(box)
            deduped.append(c)

    st.success(f"After deduplication: {len(deduped)} unique box combinations remain ✅")

    # --- Trap score ranking ---
    def trapv3_score(combo):
        hot = {'0', '1', '3'}
        cold = {'2', '4', '7'}
        due = {'5', '6'}
        prime = {'2', '3', '5', '7'}

        hot_count = sum(1 for d in combo if d in hot)
        cold_count = sum(1 for d in combo if d in cold)
        due_count = sum(1 for d in combo if d in due)
        neutral_count = 5 - (hot_count + cold_count + due_count)
        prime_count = sum(1 for d in combo if d in prime)

        return round(hot_count * 1.5 + cold_count * 1.25 + due_count * 1.0 + neutral_count * 0.5 + prime_count * 1.0, 2)

    scored = [(combo, trapv3_score(combo)) for combo in deduped]
    scored.sort(key=lambda x: x[1], reverse=True)

    for combo, score in scored:
        st.write(f"{combo} → Trap v3 Score: {score}")

    st.download_button(
        "Download Combos",
        data="\n".join(f"{combo} → Score: {score}" for combo, score in scored),
        file_name="filtered_combos_scored.txt",
        mime="text/plain"
    )
