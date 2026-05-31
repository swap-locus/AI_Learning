# game.py
# Generate the nth Fibonacci number

def fibonacci(n):
    """
    Generate the nth Fibonacci number (0-indexed).

    The Fibonacci sequence is defined as:
        F(0) = 0
        F(1) = 1
        F(n) = F(n-1) + F(n-2) for n > 1

    Args:
        n (int): The position in the Fibonacci sequence.

    Returns:
        int: The nth Fibonacci number.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def main():
    """Prompt the user for n and print the nth Fibonacci number."""
    try:
        n = int(input("Enter the position n (non-negative integer): "))
        result = fibonacci(n)
        print(f"The {n}th Fibonacci number is: {result}")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
