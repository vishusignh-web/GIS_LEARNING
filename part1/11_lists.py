# Topic 11: lists
areas = [450.5, 300.0, 725.25]
areas.append(510.0)
areas.remove(300.0)
areas[0] = 460.0

print("Areas:", areas)
print("Min:", min(areas), "Max:", max(areas), "Total:", sum(areas))
print("First two:", areas[:2], "| Last:", areas[-1])
print("Sorted desc, top 3:", sorted(areas, reverse=True)[:3])

nested = [["P1", 450.5], ["P2", 725.25]]
print("Nested:", nested[1][0], nested[1][1])
