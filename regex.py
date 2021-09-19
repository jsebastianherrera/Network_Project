import re
#r.paez,sophia.javeriana.edu.co,rpaez/
f=open("virtual_sites.txt","r")
nhost=[]
hostv=[]
root=[]
for i in f:
    r=re.findall("([a-zA-Z\.]*\,|\~[a-zA-Z]*\/)",i)
    print(r)
    nhost.append(r[0][:len(r[0])-1])
    hostv.append(r[1][:len(r[1])-1])
    root.append(r[2])

table={'Host virtual':nhost,'Host real':hostv,'Root directory':root}
print(table)
