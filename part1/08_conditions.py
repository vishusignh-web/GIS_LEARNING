# Topic 8: conditions and decision rules
def review_height(height, limit=25):
    if height < 0:
        return "Invalid height"
    elif height <= limit * 0.9:
        return "Permitted"
    elif height <= limit:
        return "Permitted (near limit)"
    else:
        return "Requires further review"

for h in [-1, 20, 24.5, 25, 25.1]:
    print(f"{h:>6} -> {review_height(h)}")
