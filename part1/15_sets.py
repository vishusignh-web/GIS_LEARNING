# Topic 15: sets
permitted = {"R1", "R2", "C1"}
found = {"R1", "R2", "I1", "R2", "X9"}           # duplicates removed automatically

print("Found:", sorted(found))                               # Found: ['I1', 'R1', 'R2', 'X9']
print("Valid:", sorted(found & permitted))                     # Valid: ['R1', 'R2']
print("Invalid:", sorted(found - permitted))                    # Invalid: ['I1', 'X9']
print("Unused permitted:", sorted(permitted - found))          # Unused permitted: ['C1']
print("All codes:", sorted(found | permitted))                 # All codes: ['C1', 'I1', 'R1', 'R2', 'X9']
codes = ["R1", "R1", "C1", "R2", "R2", "R2"]                    # duplicates removed automatically
print("Unique count:", len(set(codes)))                           # Unique count: 3
