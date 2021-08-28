import psutil

import pywinhandle

if __name__ == '__main__':
    pids = []
    for proc in psutil.process_iter():
        if proc.name() == r"chrome.exe":
            pids.append(proc.pid)
    handles = pywinhandle.find_handles(pids=pids)
    for h in handles:
        print(h)
