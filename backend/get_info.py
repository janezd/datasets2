from dataset import Dataset

from info import info

for i in info:
    d = {'location': i[0][1]} | i[1]
    element = Dataset(**d)
    element.add()


