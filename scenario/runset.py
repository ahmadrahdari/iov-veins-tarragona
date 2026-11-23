#!/usr/bin/env python3
"""Resumable batch runner.

usage: runset.py "20,40,60" [workers] [configs] [budget_minutes] [seeds]

Run numbers: r = SEEDS*index(N) + seed, for N in 20..120 and seed in 0..SEEDS-1 (SEEDS = 10,
the "repeat" of omnetpp.ini); seeds is a range such as "0-9" (default: all).
A run is complete when its log reports that the time limit was reached and
ends with "End.", and its .sca file exists;
complete runs are skipped, so the script can be restarted at any time.
With a time budget, a run is only started if it is expected to finish
before the budget expires (estimates are refined from finished runs).
A run that stops with a simulation error is marked as failed and is not
repeated until its runlogs/<cfg>_<r>.failed file is removed.
"""
import json, os, sys, time, subprocess, threading

NS_ALL = [20, 40, 60, 80, 100, 120]
CFGS_ALL = ('Proposed', 'ProposedA', 'Baseline')
SEEDS = 10
EST = {20: 6.0, 40: 12.0, 60: 19.0, 80: 27.0, 100: 35.0, 120: 45.0}   # minutes per run (2 runs in parallel)

want = set(int(x) for x in sys.argv[1].split(','))
W = int(sys.argv[2]) if len(sys.argv) > 2 else 2
CFGS = tuple(sys.argv[3].split(',')) if len(sys.argv) > 3 else CFGS_ALL
BUDGET = float(sys.argv[4]) * 60 if len(sys.argv) > 4 and float(sys.argv[4]) > 0 else None
if len(sys.argv) > 5:
    a, b = (int(x) for x in sys.argv[5].split('-'))
    SEEDS_USE = set(range(a, b + 1))
else:
    SEEDS_USE = set(range(SEEDS))
T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
os.makedirs('runlogs/claims', exist_ok=True)
os.makedirs('results', exist_ok=True)
TIMES = 'runlogs/times.json'
if os.path.exists(TIMES):
    for k, v in json.load(open(TIMES)).items():
        EST[int(k)] = v


def names(cfg, r):
    return f'runlogs/{cfg}_{r}.txt', f'results/{cfg}-N{NS_ALL[r // SEEDS]}-r{r % SEEDS}.sca'


def done(cfg, r):
    log, sca = names(cfg, r)
    if not (os.path.exists(sca) and os.path.exists(log)):
        return False
    text = open(log).read()
    # a run stopped by a signal also ends with "End." (OMNeT++ exits gracefully), so the
    # log must show that the simulation reached its time limit
    return text.rstrip().endswith('End.') and 'Simulation time limit reached' in text


def failed(cfg, r):
    return os.path.exists(f'runlogs/{cfg}_{r}.failed')


def claim(cfg, r):
    p = f'runlogs/claims/{cfg}_{r}'
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            pid = int(open(p).read().strip() or 0)
        except ValueError:
            pid = 0
        if pid and os.path.exists(f'/proc/{pid}'):
            return False
        os.remove(p)
        return claim(cfg, r)


def fits(n):
    return BUDGET is None or time.time() - T0 + EST[n] * 60 * 1.1 <= BUDGET


jobs = [(cfg, r) for r in range(6 * SEEDS) if NS_ALL[r // SEEDS] in want and r % SEEDS in SEEDS_USE
        for cfg in CFGS if not done(cfg, r) and not failed(cfg, r)]
jobs.sort(key=lambda j: (j[1] % SEEDS, NS_ALL[j[1] // SEEDS]))   # seed by seed, small N first
if os.environ.get('LARGE_FIRST'):   # packs long runs first, shorter ones into the rest of the budget
    jobs.sort(key=lambda j: (j[1] % SEEDS, -NS_ALL[j[1] // SEEDS]))
lock = threading.Lock()


def worker(w):
    while True:
        with lock:
            j = None
            for cand in list(jobs):
                if not fits(NS_ALL[cand[1] // SEEDS]):
                    continue
                jobs.remove(cand)
                if not done(*cand) and claim(*cand):
                    j = cand
                    break
            if j is None:
                return
        cfg, r = j
        n = NS_ALL[r // SEEDS]
        s = time.time()
        log, sca = names(cfg, r)
        with open(log, 'w') as f:
            rc = subprocess.run(['./run.sh', cfg, str(r)], stdout=f, stderr=subprocess.STDOUT).returncode
        try:
            os.remove(f'runlogs/claims/{cfg}_{r}')
        except OSError:
            pass
        mins = (time.time() - s) / 60
        if done(cfg, r):
            with lock:
                EST[n] = max(mins, EST[n] if os.path.exists(TIMES) else 0)
                json.dump(EST, open(TIMES, 'w'))
            print(f'done {cfg} r{r} N={n} in {mins:.1f}min', flush=True)
        else:
            open(f'runlogs/{cfg}_{r}.failed', 'w').write(f'rc={rc}\n')
            print(f'FAILED {cfg} r{r} N={n} rc={rc} after {mins:.1f}min (see {log})', flush=True)


th = [threading.Thread(target=worker, args=(w,)) for w in range(W)]
[t.start() for t in th]
[t.join() for t in th]
rem = [(c, r) for r in range(6 * SEEDS) if NS_ALL[r // SEEDS] in want and r % SEEDS in SEEDS_USE for c in CFGS if not done(c, r)]
bad = [(c, r) for (c, r) in rem if failed(c, r)]
print(f'RUNSET_END remaining {len(rem)} failed {len(bad)} elapsed {(time.time() - T0) / 60:.1f}min', flush=True)
