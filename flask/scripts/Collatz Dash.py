#!/usr/bin/env python

import argparse
from matplotlib import pyplot as plt
import datetime as dt

parser = argparse.ArgumentParser(description="An implementation of the Boston Python Collatz Dash")

parser.add_argument("-a", dest="a", type=int, required=True, help="Age of contestant A")
parser.add_argument("-b", dest="b", type=int, required=True, help="Age of contestant B")

parser.add_argument("-namea", dest="namea", type=str, default='A', help="Name of contestant A")
parser.add_argument("-nameb", dest="nameb", type=str, default='B', help="Name of contestant B")


args = parser.parse_args()

a_steps = []
b_steps = []

#    Look at your current yard line (n).
#    If n is even, immediately advance to the (n / 2) yard line.
#    If n is odd, go back (n * 3) + 1 yards.

def calculate_next_step(x):
    if x // 2 == float(x) / 2:
        return x // 2
    else:
        return (x * 3) + 1

a = args.a
b = args.b

print("Running the Collatz Dash!")
print("%s (Age %d) vs. %s (Age %d)" % (args.namea, args.a, args.nameb, args.b))
print("Ready...")
print("Get set...")
print("GO!")

while a > 1 and b > 1:
    a_steps.append(a)
    b_steps.append(b)

    a = calculate_next_step(a)
    b = calculate_next_step(b)

number_of_steps = len(a_steps)

print("Race finished in %d turns " % number_of_steps)
if a == 1:
    print("Runner '%s' won the race!" % args.namea)

elif b == 1:
    print("Runner '%s' won the race!" % args.nameb)



fig = plt.figure()
ax = fig.add_subplot(1,1,1)

ax.plot(range(number_of_steps), a_steps, 'r', label=args.namea)
ax.plot(range(number_of_steps), b_steps, 'b', label=args.nameb)

ax.set_title("Collatz Dash %d" % dt.datetime.now().year)
ax.set_ylabel('Distance to finish line')
ax.set_xlabel('Steps')

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc='best', prop={'size':20})

fig.savefig('Race.png')
    

