import psutil
import time
from memory_profiler import memory_usage


def measureCpuAndMemory(func, *args, **kwargs):
    process = psutil.Process()

    cpuBefore = process.cpu_percent(interval=None)
    memBefore = process.memory_info().rss / (1024 ** 2)

    startTime = time.time()
    memUsage = memory_usage((func, args, kwargs), interval=0.1, max_usage=True)
    endTime = time.time()

    cpuAfter = process.cpu_percent(interval=None)
    memAfter = process.memory_info().rss / (1024 ** 2)

    return {
        "executionTimeSeconds": round(endTime - startTime, 3),
        "cpuPercentDelta": round(cpuAfter - cpuBefore, 2),
        "memoryPeakMB": round(memUsage, 2),
        "memoryDeltaMB": round(memAfter - memBefore, 2)
    }
