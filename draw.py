import matplotlib.pyplot as plt
import numpy as np


with open("male.txt", 'r') as f:
  male = dict()
  for line in f.readlines():
    line = line.strip()
    age, cnt = map(int, line.split())
    male[age] = cnt

with open("female.txt", 'r') as f:
  female = dict()
  for line in f.readlines():
    line = line.strip()
    age, cnt = map(int, line.split())
    female[age] = cnt

colors = ["orange", "magenta"]
labels = ["Парни", "Девушки"]

width = 0.25
ages = set(male.keys())
ages = ages.union(set(female.keys()))
ages = np.array(sorted(list(ages)))

offset = 0

fig, ax = plt.subplots(layout="constrained")
male_bins = []
female_bins = []
for age in ages:
  male_bins.append(0 if age not in male else male[age])
  female_bins.append(0 if age not in female else female[age])

offset = 0
for name, data, color in zip(labels, (male_bins, female_bins), colors):
  offset += width
  rects = ax.bar(ages + offset, data, width, edgecolor="black", linewidth=3, label=name, color=color)
  ax.bar_label(rects, padding=3, size=25)

ax.set_ylabel("Количество", size=50)
ax.set_xlabel("Возраст", size=50)
ax.set_title("Распределение возраста по полу на дайвинчике Курск", size=50)
ax.set_yticks([])
ax.set_xticks(ages + 1.5 * width, ages, size=50)
ax.legend(prop={"size": 50}, loc="upper right")
plt.show()
