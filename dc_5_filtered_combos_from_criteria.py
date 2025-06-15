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

# --- Historical Seed-to-Winner Sum Mapping ---
seed_sum_to_valid_winner_sums = {
    11: {14, 15}, 12: {15, 16}, 13: {16, 17}, 14: {16, 17, 18}, 15: {14, 15, 16, 17},
    16: {15, 16, 17}, 17: {16, 17, 18}, 18: {16, 17, 19}, 19: {17, 19, 20}, 20: {18, 20, 21},
    21: {19, 20, 21, 22}, 22: {20, 21, 22, 23}, 23: {21, 22, 23, 24}, 24: {22, 23, 24, 25},
    25: {23, 24, 25}, 26: {24, 25, 26, 27}, 27: {25, 26, 27, 28}, 28: {26, 27, 28},
    29: {27, 28, 29, 30}, 30: {28, 29, 30, 31}, 31: {29, 30, 31, 32}, 32: {30, 31, 32, 33},
    33: {31, 32, 33, 34}, 34: {32, 33, 34}, 35: {33, 34, 35}, 36: {34, 35, 36}
}

# --- Toggles for filters ---
st.markdown("### Filters (click to activate)")
run_filters = st.checkbox("✅ Apply all filters (recommended)", value=False)
exclude_triples = st.checkbox("Eliminate Triples", help="Remove combos with 3 of the same digit")
apply_spread_filter = st.checkbox("Digit Spread < 4", help="Eliminates combos with small spread between digits")
apply_mirror_filter = st.checkbox("Mirror Count < 2", help="Requires at least 2 mirror digits from input set")
apply_high_digit_filter = st.checkbox("Max 2 digits ≥ 8", help="Limits combos with many high digits")
apply_vtrac_filter = st.checkbox("No 4+ V-Trac repeats", help="Removes combos with too many digits in one V-Trac group")
apply_prime_filter = st.checkbox("3+ Prime Digits", help="Eliminates combos with 3 or more of 2, 3, 5, 7")
apply_sum_trap_filter = st.checkbox("Sum ends in 0 or 5", help="Eliminates combos whose sum ends in 0 or 5")
apply_mirror_sum_filter = st.checkbox("Mirror Sum = Digit Sum", help="Digit sum shouldn't equal mirror sum")
apply_uniform_vtrac_filter = st.checkbox("All Same V-Trac Group", help="Removes combos with all digits in same group")

if all([hot, cold, due, seed]):
    hot_digits = set(hot.split(","))
    cold_digits = set(cold.split(","))
    due_digits = set(due.split(","))
    seed_digits = set(seed.split(","))
    all_digits = list(set(hot_digits | cold_digits | due_digits | seed_digits))

    seed_sum = sum(map(int, seed_digits))
    valid_sums = seed_sum_to_valid_winner_sums.get(seed_sum, set())

    st.markdown(f"**Seed Sum:** {seed_sum} → Valid Winner Sums: {sorted(valid_sums)}")

    candidates = []
    removed_by_filter = Counter()
    filter_application_count = Counter()

    for combo in itertools.product(all_digits, repeat=5):
        digits = list(combo)
        digit_counts = Counter(digits)
        digit_sum = sum(map(int, digits))

        if digit_sum not in valid_sums:
            continue

        passed = True
        reason = None
        filter_application_count['Initial'] += 1

        if not run_filters:
            candidates.append("".join(digits))
            continue

        if sum(d in seed_digits for d in digits) < 2:
            passed = False
            reason = "<2 seed digits"
        elif sum(d in (hot_digits | cold_digits | due_digits) for d in digits) < 2:
            passed = False
            reason = "<2 from H/C/D"
        elif max(digit_counts.values()) >= 4:
            passed = False
            reason = "Quad/Quint"
        elif exclude_triples and max(digit_counts.values()) >= 3:
            passed = False
            reason = "Triple"
        elif apply_mirror_sum_filter and digit_sum == sum([9 - int(d) for d in digits]):
            passed = False
            reason = "Mirror = Sum"
        elif apply_uniform_vtrac_filter and len(set(int(d) % 5 for d in digits)) == 1:
            passed = False
            reason = "Uniform V-Trac"
        elif apply_prime_filter and len(set(d for d in digits if d in {"2", "3", "5", "7"})) >= 3:
            passed = False
            reason = "3+ Primes"
        elif apply_high_digit_filter and sum(1 for d in digits if int(d) >= 8) >= 2:
            passed = False
            reason = "High Digits"
        elif apply_sum_trap_filter and digit_sum % 10 in {0, 5}:
            passed = False
            reason = "Sum Ends 0/5"
        elif apply_spread_filter and (max(map(int, digits)) - min(map(int, digits))) < 4:
            passed = False
            reason = "Spread < 4"
        elif apply_mirror_filter and sum(d in {"0","1","2","3","4","5","6","7","8","9"} for d in digits) < 2:
            passed = False
            reason = "<2 Mirror Digits"
        elif apply_vtrac_filter and max(Counter([int(d)%5 for d in digits]).values()) >= 4:
            passed = False
            reason = "4+ V-Trac Repeats"

        if passed:
            candidates.append("".join(digits))
        else:
            removed_by_filter[reason] += 1

    st.write(f"✅ **After Filters:** {len(candidates)} combos")
    for reason, count in removed_by_filter.items():
        st.write(f"🚫 {reason}: {count} removed")

    seen = set()
    deduped = []
    for c in candidates:
        box = "".join(sorted(c))
        if box not in seen:
            seen.add(box)
            deduped.append(c)

    st.success(f"✅ **After Deduplication:** {len(deduped)} unique box combos")

    if st.button("Run Trap v3 Scoring"):
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
