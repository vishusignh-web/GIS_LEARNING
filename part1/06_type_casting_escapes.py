# Topic 6: type casting and escape sequences
area_text = "450.75"
try:
    area = float(area_text)
except ValueError:
    print("Area must be a number")
else:
    print("PARCEL REPORT\n\tArea:\t" + str(area) + " m2\n\tNote:\t\"Checked\"")

for text in ["true", "false", "yes"]:
    print(text, "->", text.strip().lower() == "true")   # explicit Boolean interpretation
print("bool('false') is", bool("false"), "(any non-empty string is True!)")
print("Path example: C:\\gis\\data")
print(int("42"), float("3.5"), str(7))
try:
    int("abc")
except ValueError as e:
    print("Invalid conversion:", e)
