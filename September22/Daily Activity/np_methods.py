import numpy as np
arr=np.array([10,20,30,40,50])

print("Max marks: ",arr.max())
print("Min marks: ",arr.min())
print("Average marks: ",arr.mean())

print("First three elements: ",arr[:3])
print("Reversed array: ", arr[::-1])
print("Sum: ", np.sum(arr))
print("Standard deviation: ", np.std(arr))
