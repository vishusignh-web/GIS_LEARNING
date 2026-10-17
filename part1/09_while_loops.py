# Topic 9: while loops
attempts, max_attempts = 0, 5
while attempts < max_attempts:
    text = input("Enter parcel area (m2): ")
    attempts += 1
    try:
        area = float(text)
    except ValueError:
        print(f"Not a number. {max_attempts - attempts} attempts left.")
        continue
    if area <= 0:
        print("Area must be positive.")
        continue
    print(f"Accepted: {area}")
    break
else:
    print("Too many invalid attempts.")
