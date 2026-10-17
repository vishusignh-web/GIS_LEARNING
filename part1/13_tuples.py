# Topic 13: tuples
point = (55.2708, 25.2048)           # (x, y) = (longitude, latitude)
x, y = point
print(f"x={x}, y={y}")
print(point[0], len(point), point.count(25.2048))

def min_max(values):
    return min(values), max(values)   # returns a tuple

low, high = min_max([450.5, 300.0, 725.25])
print("min/max:", low, high)

try:
    point[0] = 1
except TypeError as e:
    print("Tuples are immutable:", e)
