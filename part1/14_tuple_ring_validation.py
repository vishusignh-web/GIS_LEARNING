# Topic 14: validate a polygon ring before sending it to ArcGIS
def validate_ring(ring):
    if len(ring) < 4:
        return False, "A ring needs at least 4 points"
    for i, vertex in enumerate(ring):
        if not (isinstance(vertex, tuple) and len(vertex) == 2):
            return False, f"Vertex {i} must be an (x, y) tuple"
        if not all(isinstance(c, (int, float)) for c in vertex):
            return False, f"Vertex {i} has non-numeric coordinates"
    if ring[0] != ring[-1]:
        return False, "Ring is not closed"
    for a, b in zip(ring, ring[1:]):
        if a == b:
            return False, f"Duplicate consecutive vertex {a}"
    return True, "OK"

ring = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]
print(validate_ring(ring))                       # (True, 'OK')
print(validate_ring(ring[:-1]))                  # not closed
print(validate_ring([(0, 0), (0, 0), (1, 1), (0, 0)])) #(False, 'Duplicate consecutive vertex (0, 0)')
print("(10, 10) in ring:", (10, 10) in ring)
for i, (x, y) in enumerate(ring):
    print(f"vertex {i}: x={x}, y={y}")
