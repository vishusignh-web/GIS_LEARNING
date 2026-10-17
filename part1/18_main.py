# Topic 18: main entry-point pattern (uses gis_calc.py)
from gis_calc import m2_to_hectares, check_height

def main():
    print(m2_to_hectares(25000))
    print(check_height(22))

if __name__ == "__main__":
    main()
