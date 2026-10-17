# Topic 12: list comprehensions
areas = [450.5, 300.0, 725.25, 980.0]
minimum = 500

large = [a for a in areas if a > minimum]
hectares = [round(a / 10000, 4) for a in areas]
labels = [f"{a:.1f} m2" for a in areas]

large_loop = []                      # same result with a normal loop
for a in areas:
    if a > minimum:
        large_loop.append(a)

print(large, large == large_loop)
print(hectares)
print(labels)
