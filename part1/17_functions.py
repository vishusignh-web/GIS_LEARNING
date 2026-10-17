# Topic 17: functions
def m2_to_hectares(area_m2, decimals=2):
    return round(area_m2 / 10000, decimals)

def hectares_to_m2(area_ha):
    return area_ha * 10000

def check_height(height, limit=25):
    return "Permitted" if height <= limit else "Requires further review"

print(m2_to_hectares(25000))
print(check_height(26))
print(check_height(26, limit=30))
assert hectares_to_m2(m2_to_hectares(25000)) == 25000
print("Round trip OK")
