# Topic 5: keyboard input and multiple values
raw = input("Enter parcel ID, zoning, area (separated by spaces): ")
parts = raw.split()

if len(parts) != 3:
    print("Please enter exactly 3 values.")
else:
    parcel_id, zoning, area = parts
    print(f"ID={parcel_id}, Zone={zoning}, Area={area}")
