def multiplication_table(num):
    print(f"Multiplication table of {num}")
    for i in range(1,11):
        print(f"{num} x {i} = {num*i}")

num=int(input("Enter a number: "))
print(multiplication_table(num))