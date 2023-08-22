# Read input values from the user
dx, dy, k = map(int, input("Enter dx, dy, and k: ").split())

# Initialize crystal structures
minimal_structure = [['.' for _ in range(dy)] for _ in range(dx)]
maximal_structure = [['#' for _ in range(dy)] for _ in range(dx)]

# Process wind observations
for _ in range(k):
    wx, wy, b = map(int, input("Enter wx, wy, and b: ").split())
    for _ in range(b):
        x, y = map(int, input("Enter x and y for boundary: ").split())
        minimal_structure[x - wx - 1][y - wy - 1] = '#'
        maximal_structure[x - wx - 1][y - wy - 1] = '.'

# Print the minimal structure
for row in minimal_structure:
    print(''.join(row))

print()  # Print an empty line

# Print the maximal structure
for row in maximal_structure:
    print(''.join(row))