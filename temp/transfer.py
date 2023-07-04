import re

with open(r'D:\Note\GithubClone\JavaNote\SSM.md', 'r', encoding='utf-8') as f:
    content = f.read()
out = False
while True:
    s = re.search(r'(# (\w+).*?)\s+\*+\s+# ', content, re.S)
    try:
        content = content.replace(s.groups()[0], '')
    except AttributeError:
        s = re.search(r'(# (\w+).*)', content, re.S)
        out = True

    print(s.groups()[1])
    with open(rf'D:\Note\Framework\{s.groups()[1]}.md', 'w', encoding='utf-8') as f:
        f.write(s.groups()[0])
    if out:
        break
