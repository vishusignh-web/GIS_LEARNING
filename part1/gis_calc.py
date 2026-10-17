# Topic 18: reusable module
def m2_to_hectares(area_m2, decimals=2):
    return round(area_m2 / 10000, decimals)

def check_height(height, limit=25):
    return height <= limit
