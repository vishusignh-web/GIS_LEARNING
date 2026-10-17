# Topic 7: operators and calculations
area_m2 = 25000
area_ha = round(area_m2 / 10000, 2)
permitted = ["R1", "R2", "C1"]
zone = "R2"

print(f"{area_m2} m2 = {area_ha} ha")
print("Permitted:", zone in permitted)
print("Not permitted:", zone not in permitted)
print("Large and permitted:", (area_ha > 2) and (zone in permitted))

total = 0
total += area_m2
total += 1500
print("Total:", total, "| floor div:", total // 1000, "| remainder:", total % 1000)
print("Precedence:", 2 + 3 * 4, "vs", (2 + 3) * 4)
