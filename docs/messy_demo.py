# Messy shop script for demoing the OOP refactor
items = []
prices = {}
def add(n, t, p, q):
    items.append([n, t, p, q])
    prices[n] = p
def total():
    s = 0
    for i in range(len(items)):
        if items[i][1] == "food":
            s = s + items[i][2] * items[i][3] * 1.05
        elif items[i][1] == "tech":
            s = s + items[i][2] * items[i][3] * 1.18
        elif items[i][1] == "book":
            s = s + items[i][2] * items[i][3]
        else:
            s = s + items[i][2] * items[i][3] * 1.1
    return s
def discount(t, code):
    if code == "SAVE10":
        return t - t * 0.1
    if code == "HALF":
        return t / 2
    return t
def show():
    for i in items:
        print(i[0] + " x" + str(i[3]) + " = " + str(i[2] * i[3]))
def find(n):
    for i in range(len(items) + 1):
        if items[i][0] == n:
            return items[i]
add("rice", "food", 50, 2)
add("laptop", "tech", 40000, 1)
add("novel", "book", 300, 3)
show()
print(discount(total(), "HALF"))
print(find("pen"))
