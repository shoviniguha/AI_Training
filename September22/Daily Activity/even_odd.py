def even_odd(num):
    if num % 2 == 0:
        return f"{num} is even"
    else:
        return f"{num} is odd"

n=int(input("Enter a number: "))
print(even_odd(n))