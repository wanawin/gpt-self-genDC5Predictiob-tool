import streamlit as st
import itertools
from collections import Counter
from datetime import datetime
import pandas as pd
# removed matplotlib due to deployment limitations

st.set_page_config(page_title="DC-5 Guided Combo Generator", layout="wide")
st.title("🎯 DC-5 Combo Generator by Filter Rules Only")

hot = st.text_input("Enter hot digits (comma-separated):")
cold = st.text_input("Enter cold digits (comma-separated):")
due = st.text_input("Enter due digits (comma-separated):")
seed = st.text_input("Enter seed digits (comma-separated):")

seed_sum_to_valid_winner_sums = {
    11: {14, 15}, 12: {15, 16}, 13: {16, 17}, 14: {16, 17, 18}, 15: {14, 15, 16, 17},
    16: {15, 16, 17}, 17: {16, 17, 18}, 18: {16, 17, 19}, 19: {17, 19, 20}, 20: {18, 20, 21},
    21: {19, 20, 21, 22}, 22: {20, 21, 22, 23}, 23: {21, 22, 23, 24}, 24: {22, 23, 24, 25},
    25: {23, 24, 25}, 26: {24, 25, 26, 27}, 27: {25, 26, 27, 28}, 28: {26, 27, 28},
    29: {27, 28, 29, 30}, 30: {28, 29, 30, 31}, 31: {29, 30, 31, 32}, 32: {30, 31, 32, 33},
    33: {31, 32, 33, 34}, 34: {32, 33, 34}, 35: {33, 34, 35}, 36: {34, 35, 36}
}

percentile_winner_sums = set(range(15, 33))
sum_rankings = [17, 16, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

filter_log = []

def log_filter_step(name, count):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filter_log.append(f"[{ts}] {name}: {count} combos remain\n")

if all([hot, cold, due, seed]):
    hot_digits = set(hot.split(","))
    cold_digits = set(cold.split(","))
    due_digits = set(due.split(","))
    seed_digits = seed.split(",")  # List form preserves duplicates for correct sum calculation
    all_digits = list(set(hot_digits | cold_digits | due_digits | set(seed_digits)))

    seed_sum = sum(map(int, seed_digits))
    valid_sums = seed_sum_to_valid_winner_sums.get(seed_sum, set())
    st.markdown(f"🔁 **Seed Sum = {seed_sum} → Valid Winner Sums = {sorted(valid_sums)}**")

    st.markdown("### 🚦 Automatic Filters (always applied)")
    candidates = []
    removed_by_filter = Counter()

    for combo in itertools.product(all_digits, repeat=5):
        digits = list(combo)
        digit_counts = Counter(digits)
        digit_sum = sum(map(int, digits))

        if digit_sum not in valid_sums:
            removed_by_filter["Outside Seed-to-Winner Sum Map"] += 1
            continue
        if sum(d in seed_digits for d in digits) < 2:
            removed_by_filter["<2 seed digits"] += 1
            continue
        if sum(d in (hot_digits | cold_digits | due_digits) for d in digits) < 2:
            removed_by_filter["<2 from H/C/D"] += 1
            continue
        if max(digit_counts.values()) >= 4:
            removed_by_filter["Quad/Quint"] += 1
            continue

        candidates.append("".join(digits))

    st.markdown(f"✅ **After Auto Filters:** {len(candidates)} combos")
    log_filter_step("After Auto Filters", len(candidates))
    for reason, count in removed_by_filter.items():
        st.markdown(f"🚫 {reason}: {count} removed")

    st.markdown("### 🧪 Manual Filters")
    exclude_triples = st.checkbox("Eliminate Triples")
    apply_spread_filter = st.checkbox("Digit Spread < 4")
    apply_high_digit_filter = st.checkbox("Max 2 digits ≥ 8")
    apply_prime_filter = st.checkbox("3+ Prime Digits")

    filtered_manual = []
    removed_manual = Counter()
    for c in candidates:
        digits = list(c)
        digit_counts = Counter(digits)
        if exclude_triples and max(digit_counts.values()) >= 3:
            removed_manual["Triple"] += 1
            continue
        if apply_spread_filter and (max(map(int, digits)) - min(map(int, digits))) < 4:
            removed_manual["Spread < 4"] += 1
            continue
        if apply_high_digit_filter and sum(1 for d in digits if int(d) >= 8) >= 2:
            removed_manual["High Digits"] += 1
            continue
        if apply_prime_filter and len([d for d in digits if d in {"2", "3", "5", "7"}]) >= 3:
            removed_manual["3+ Primes"] += 1
            continue
        filtered_manual.append(c)

    st.markdown(f"✅ After Manual Filters: {len(filtered_manual)} combos")
    log_filter_step("After Manual Filters", len(filtered_manual))
    for reason, count in removed_manual.items():
        st.markdown(f"🛑 {reason}: {count} removed")

    seen = set()
    deduped = []
    for c in filtered_manual:
        box = "".join(sorted(c))
        if box not in seen:
            seen.add(box)
            deduped.append(c)

    st.success(f"✅ **After Deduplication:** {len(deduped)} unique box combos")
    log_filter_step("After Deduplication", len(deduped))

    st.markdown("### 📊 Post-Deduplication: Top Winner Percentile Filter")
    filtered_by_percentile = [c for c in deduped if sum(map(int, c)) in percentile_winner_sums]
    st.info(f"✅ After Winner Percentile Filter: {len(filtered_by_percentile)} combos")
    log_filter_step("After Percentile Filter", len(filtered_by_percentile))

    st.markdown("### ✂️ Manual Winner Sum Filters (Ranked by Likelihood)")
    selected_sums = []
    for s in sum_rankings:
        if s in valid_sums:
            checked = True if sum_rankings.index(s) < 3 else False
            if st.checkbox(f"Sum {s} [#{sum_rankings.index(s)+1}]", value=checked):
                selected_sums.append(s)

    final_combos = [c for c in filtered_by_percentile if sum(map(int, c)) in selected_sums]
    st.success(f"✅ Final Combo Count After Manual Sum Trim: {len(final_combos)}")
    log_filter_step("After Manual Sum Trim", len(final_combos))

    if st.button("📈 Run Trap v3 Scoring"):
        def trapv3_score(combo):
            hot_set = {'0', '1', '3'}
            cold_set = {'2', '4', '7'}
            due_set = {'5', '6'}
            prime = {'2', '3', '5', '7'}
            hot_count = sum(1 for d in combo if d in hot_set)
            cold_count = sum(1 for d in combo if d in cold_set)
            due_count = sum(1 for d in combo if d in due_set)
            neutral_count = 5 - (hot_count + cold_count + due_count)
            prime_count = sum(1 for d in combo if d in prime)
            return round(hot_count * 1.5 + cold_count * 1.25 + due_count * 1.0 + neutral_count * 0.5 + prime_count * 1.0, 2)

        scored = [(combo, trapv3_score(combo)) for combo in final_combos]
        scored.sort(key=lambda x: x[1], reverse=True)

        scores = [score for _, score in scored]
        min_score = min(scores)
        max_score = max(scores)
        score_cutoff = st.slider("Minimum Trap v3 Score", min_value=min_score, max_value=max_score, value=min_score, step=0.25)

        filtered_scored = [(combo, score) for combo, score in scored if score >= score_cutoff]
        st.markdown(f"✅ Combos after score filter (≥ {score_cutoff}): {len(filtered_scored)}")

        st.markdown("### 📊 Trap Score Distribution")
        st.markdown("### 🏆 Top 5 Highest-Scoring Combos")
        top5 = filtered_scored[:5]
        for i, (combo, score) in enumerate(top5, 1):
            st.write(f"#{i}: {combo} → Score: {score}")

        st.bar_chart(pd.Series(scores).value_counts().sort_index())

        st.markdown("### ⭐ Scored Combos")
        for combo, score in filtered_scored:
            st.write(f"{combo} → Trap v3 Score: {score}")

        df = pd.DataFrame(filtered_scored, columns=["Combo", "Score"])
        df["Rank"] = df["Score"].rank(method="first", ascending=False).astype(int)

        st.download_button(
            label="📥 Download Scored Combos (.txt)",
            data="\n".join(f"{combo} → Score: {score}" for combo, score in filtered_scored),
            file_name="scored_combos.txt",
            mime="text/plain"
        )
        st.download_button(
            label="📊 Download Scored Combos (.csv)",
            data=df.to_csv(index=False),
            file_name="scored_combos.csv",
            mime="text/csv"
        )

    if st.button("📄 Download Filter Log"):
        filename = f"filter_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.download_button(
            label="Download Filter Log (.txt)",
            data="".join(filter_log),
            file_name=filename,
            mime="text/plain"
        )
