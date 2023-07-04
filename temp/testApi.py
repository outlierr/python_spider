import re

a = "222ABC33"
af = re.findall("[ABCD]{2,4}", a)
print(af)
