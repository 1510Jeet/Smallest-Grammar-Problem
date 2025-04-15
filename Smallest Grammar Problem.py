import random
import time
from collections import defaultdict
import matplotlib.pyplot as plt
import string

# Grammar class for all algorithms
class Grammar:
    def __init__(self):
        self.rules = {}
        self.next_nt = 0

    def add_rule(self, s):
        nt = f'A{self.next_nt}'
        self.rules[nt] = s
        self.next_nt += 1
        return nt

    def size(self):
        return sum(len(r) for r in self.rules.values())

# 1. LZ78
def lz78(s):
    g = Grammar()
    d = {}
    i = 0
    while i < len(s):
        prefix = ''
        j = i
        while j < len(s) and prefix + s[j] in d:
            prefix += s[j]
            j += 1
        if j < len(s):
            phrase = prefix + s[j]
            j += 1
        else:
            phrase = prefix
        if phrase not in d:
            nt = g.add_rule(phrase)
            d[phrase] = nt
        i = j
    return g

# 2. BISECTION
def bisection(s):
    g = Grammar()
    def recurse(start, end):
        if end - start <= 1:
            return s[start:end]
        mid = (start + end) // 2
        left = recurse(start, mid)
        right = recurse(mid, end)
        concat = left + right
        if concat in g.rules.values():
            for nt, val in g.rules.items():
                if val == concat:
                    return nt
        return g.add_rule(concat)

    recurse(0, len(s))
    return g

# 3. SEQUENTIAL
def sequential(s):
    g = Grammar()
    freq = defaultdict(int)

    # Count all substring frequencies up to length 5
    for l in range(1, 6):
        for i in range(len(s) - l + 1):
            sub = s[i:i + l]
            freq[sub] += 1

    i = 0
    result = []

    while i < len(s):
        best_sub = s[i]
        best_len = 1
        max_score = 0

        for l in range(1, 6):
            if i + l > len(s):
                break
            sub = s[i:i + l]
            count = freq[sub]
            score = count * (len(sub) - 1)  # Heuristic for compression benefit
            if score > max_score:
                max_score = score
                best_sub = sub
                best_len = len(sub)

        # Add rule if not already added
        if best_sub not in g.rules.values():
            nt = g.add_rule(best_sub)
        else:
            for nt, val in g.rules.items():
                if val == best_sub:
                    break
        result.append(nt)
        i += best_len

    g.add_rule(''.join(result))
    return g

# 4. RE_PAIR
def re_pair(s):
    g = Grammar()
    text = list(s)

    while True:
        freq = defaultdict(int)

        # Count all adjacent pairs
        for i in range(len(text) - 1):
            pair = (text[i], text[i + 1])
            freq[pair] += 1

        if not freq:
            break

        max_pair = max(freq, key=freq.get)
        if freq[max_pair] < 2:
            break  # No pair appears more than once

        # Add new rule
        nt = g.add_rule(''.join(max_pair))

        # Replace all occurrences of max_pair
        new_text = []
        i = 0
        while i < len(text):
            if i < len(text) - 1 and (text[i], text[i + 1]) == max_pair:
                new_text.append(nt)
                i += 2
            else:
                new_text.append(text[i])
                i += 1
        text = new_text

    g.add_rule(''.join(text))
    return g

# 5. NOVEL_LOG3N (with pair precompression)
def novel_log3n(s):
    g = Grammar()
    value_to_nt = {}
    text = list(s)
    # Precompress frequent pairs (up to 5 iterations)
    for _ in range(5):
        freq = defaultdict(int)
        for i in range(len(text) - 1):
            pair = (text[i], text[i + 1])
            freq[pair] += 1
        if not freq or max(freq.values()) < 2:
            break
        max_pair = max(freq, key=freq.get)
        nt = g.add_rule(''.join(max_pair))
        value_to_nt[''.join(max_pair)] = nt
        new_text = []
        i = 0
        while i < len(text):
            if i < len(text) - 1 and (text[i], text[i + 1]) == max_pair:
                new_text.append(nt)
                i += 2
            else:
                new_text.append(text[i])
                i += 1
        text = new_text
    text = ''.join(text)
    # Recursive decomposition
    reuse_count = 0
    def decompose(start, end):
        nonlocal reuse_count
        if end - start <= 1:
            return text[start:end]
        mid = (start + end) // 2
        left = decompose(start, mid)
        right = decompose(mid, end)
        concat = left + right
        if concat in value_to_nt:
            reuse_count += 1
            return value_to_nt[concat]
        nt = g.add_rule(concat)
        value_to_nt[concat] = nt
        return nt
    nt = decompose(0, len(text))
    g.add_rule(nt)
    print(f"  NOVEL_LOG3N: Reused {reuse_count} concatenations")
    return g


# Generate random string with a-z
def generate_random_string(size):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))

# Run simulation
def run_simulation():
    algos = {
        'LZ78': lz78,
        'BISECTION': bisection,
        'SEQUENTIAL': sequential,
        'RE_PAIR': re_pair,
        'NOVEL_LOG3N': novel_log3n,
    }
    sizes = [10, 100, 1000,10000]  # Smaller sizes for a-z
    results = defaultdict(list)
    timeout = 10  # Seconds

    for n in sizes:
        print(f"\nProcessing size {n}...")
        s = generate_random_string(n)
        for name, algo in algos.items():
            print(f"  Running {name}...")
            try:
                start = time.time()
                g = algo(s)
                elapsed = time.time() - start
                size = g.size()
                rule_count = len(g.rules)
                results[name].append((n, size, elapsed, rule_count))
                print(f"    Size = {size}, Rules = {rule_count}, Time = {elapsed:.2f}s")
            except Exception as e:
                print(f"    Failed: {e}")
                results[name].append((n, float('inf'), 0, 0, 0, 0))
    
    return results

# Plot results
def plot_results(results):
    plt.figure(figsize=(12, 8))
    plotted_any = False
    for name, data in results.items():
        ns, sizes, _, _ = zip(*data)
        valid_ns = [n for n, s in zip(ns, sizes) if s != float('inf')]
        valid_sizes = [s for s in sizes if s != float('inf')]
        if valid_ns:
            plt.plot(valid_ns, valid_sizes, label=name, marker='o')
            plotted_any = True
            print(f"Plotted {name} with sizes: {valid_sizes}")
        else:
            print(f"No valid data for {name}")
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Input Size (n)')
    plt.ylabel('Grammar Size')
    plt.title('Grammar Size vs Input Size for Random Strings (Alphabet: a-z)')
    if plotted_any:
        plt.legend()
    else:
        plt.text(0.5, 0.5, 'No valid data to plot.\nCheck algorithm outputs or timeouts.',
                 horizontalalignment='center', verticalalignment='center', transform=plt.gca().transAxes)
    plt.grid(True, which="both", ls="--")
    plt.show()

# Main execution
if __name__ == "__main__":
    results = run_simulation()
    plot_results(results)
    print("\nSimulation Complete.")