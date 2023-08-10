# type:ignore
from collections import defaultdict as dd
import os
import statistics


def scan():
    running = dd(int)
    times = dd(list[float])
    cnt = dd(int)

    def gather(file):
        lines = open(file, "rt", encoding="utf-8").readlines()
        # print(lines)
        for line in lines:
            if line.startswith("[+] "):
                # print(line)
                running[line[4:].strip()] += 1
            elif line.startswith("[-] "):
                # print(line)
                _, name, _time, time, _returned, *returned = line.split()
                # print(name)
                if time.endswith("µs"):
                    time = float(time[:-2]) / 1000000
                    pass
                elif time.endswith("ms"):
                    time = float(time[:-2]) / 1000
                elif time.endswith("ns"):
                    time = float(time[:-2]) / 1000000000
                else:
                    time = float(time[:-1])
                    print("HERE", time)
                cnt[name] += 1
                times[name].append(time)
                # exit()
                running[line[4:].split()[0]] -= 1

    for path, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".log"):
                gather(os.path.join(path, file))

    print("Still running :")
    for name in running:
        if running[name] > 0:
            print(name, running[name])

    print()
    print("Stats")
    longest = [0] * 6
    for name in times:
        total_time = sum(times[name])
        avg_time = total_time / cnt[name]
        median_time = statistics.median(times[name])
        max_time = max(times[name])
        l = [0] * 6
        l[0] = len(name)
        l[1] = len(f"{cnt[name]}")
        l[2] = len(f"{avg_time:.2f}")
        l[3] = len(f"{total_time:.2f}")
        l[4] = len(f"{median_time:.2f}")
        l[5] = len(f"{max_time:.2f}")

        for i in range(6):
            longest[i] = max(longest[i], l[i])

    for name in times:
        total_time = sum(times[name])
        avg_time = total_time / cnt[name]
        median_time = statistics.median(times[name])
        max_time = max(times[name])
        l = [0] * 6
        l[0] = len(name)
        l[1] = len(f"{cnt[name]}")
        l[2] = len(f"{avg_time:.2f}")
        l[3] = len(f"{total_time:.2f}")
        l[4] = len(f"{median_time:.2f}")
        l[5] = len(f"{max_time:.2f}")

        print(
            f"{name}{' '*(longest[0]-l[0])} cnt {' '*(longest[1]-l[1])}{cnt[name]}, avg time {' '*(longest[2]-l[2])}{avg_time:.2f} total_time {' '*(longest[3]-l[3])}{total_time:.2f}, median time {' '*(longest[4]-l[4])}{median_time:.2f}, max time {' '*(longest[5]-l[5])}{max_time:.2f}"
        )
