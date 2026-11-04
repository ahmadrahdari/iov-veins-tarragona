#!/usr/bin/env python3
# usage: runset.py "20,40,60,80" [workers]
import os, sys, time, subprocess, threading
NS_ALL = [20, 40, 60, 80, 100, 120]
want = set(int(x) for x in sys.argv[1].split(','))
W = int(sys.argv[2]) if len(sys.argv) > 2 else 2
os.chdir('/home/claude/sim/scenario')
os.makedirs('runlogs30/claims', exist_ok=True)
def done(cfg, r):
    log = f'runlogs30/{cfg}_{r}.txt'; sca = f'results/{cfg}-N{NS_ALL[r//3]}-r{r%3}.sca'
    return os.path.exists(sca) and os.path.exists(log) and open(log).read().rstrip().endswith('End.')
def claim(cfg, r):
    p = f'runlogs30/claims/{cfg}_{r}'
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd); return True
    except FileExistsError:
        try: pid = int(open(p).read().strip() or 0)
        except ValueError: pid = 0
        if pid and os.path.exists(f'/proc/{pid}'): return False
        os.remove(p); return claim(cfg, r)
jobs = [(cfg, r) for r in range(18) if NS_ALL[r//3] in want for cfg in ('Proposed','ProposedA','Chen') if not done(cfg, r)]
jobs.sort(key=lambda j: NS_ALL[j[1]//3])   # small N first
lock = threading.Lock()
def worker(w):
    while True:
        with lock:
            j = None
            for cand in list(jobs):
                jobs.remove(cand)
                if not done(*cand) and claim(*cand): j = cand; break
            if j is None: return
        cfg, r = j; s = time.time()
        with open(f'runlogs30/{cfg}_{r}.txt', 'w') as f:
            subprocess.run(['./run.sh', cfg, str(r)], stdout=f, stderr=subprocess.STDOUT)
        try: os.remove(f'runlogs30/claims/{cfg}_{r}')
        except OSError: pass
        print(f'done {cfg} r{r} N={NS_ALL[r//3]} in {(time.time()-s)/60:.1f}min', flush=True)
th = [threading.Thread(target=worker, args=(w,)) for w in range(W)]
[t.start() for t in th]; [t.join() for t in th]
rem = [(c,r) for r in range(18) if NS_ALL[r//3] in want for c in ('Proposed','ProposedA','Chen') if not done(c,r)]
print('RUNSET_END remaining', len(rem), flush=True)
