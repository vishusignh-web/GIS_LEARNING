# Topic 10: for loops
heights = [12.0, 18.5, 26.0, 31.2, 24.9]
limit = 25
count, total = 0, 0.0

for i, h in enumerate(heights, start=1):
    total += h
    if h > limit:
        count += 1
        print(f"Building {i} exceeds limit: {h}")

print("Total exceeding:", count)
print("Average height:", round(total / len(heights), 2))
for n in range(1, 4):
    print("Block", n)
for ch in "R1":
    print("char:", ch)
