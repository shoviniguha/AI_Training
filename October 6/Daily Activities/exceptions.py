try:
    n=int(input("enter number: "))
    print(10/n)
except ValueError:
    print("please enter a valid number")
except ZeroDivisionError:
    print("cannot divide by zero")
finally:
    print("all done")