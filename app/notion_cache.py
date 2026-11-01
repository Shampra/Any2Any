"""Bounded in-memory read checkpoint; no credentials or disk persistence."""
from concurrent.futures import Future,TimeoutError
from copy import deepcopy
import json
import threading

class ReadCache:
    def __init__(self,limit=32*1024*1024):
        self.lock=threading.Lock();self.values={};self.pending={};self.size=0;self.limit=limit;self.hits=0
    def read(self,key,load,check):
        with self.lock:
            if key in self.values:self.hits+=1;return deepcopy(self.values[key])
            future=self.pending.get(key);owner=future is None
            if owner:future=Future();self.pending[key]=future
        if not owner:
            while True:
                check()
                try:value=future.result(timeout=.1);break
                except TimeoutError:
                    if future.done():raise
                    continue
            with self.lock:self.hits+=1
            return deepcopy(value)
        try:
            value=load();size=len(json.dumps(value,ensure_ascii=False).encode())
            with self.lock:
                if self.size+size<=self.limit:self.values[key]=deepcopy(value);self.size+=size
            future.set_result(value);return value
        except BaseException as exc:future.set_exception(exc);raise
        finally:
            with self.lock:self.pending.pop(key,None)


def session_cache(session):
    """Share reads for 30 minutes, bounded by memory and invalidated by refresh.

    No per-entry expiry during a job: a retry must not lose the earliest reads.
    """
    import time
    now=time.monotonic();checkpoint=session.get('read_checkpoint')
    if not checkpoint or now-checkpoint['created']>=1800:
        checkpoint={'cache':ReadCache(),'updated':now,'created':now};session['read_checkpoint']=checkpoint
    checkpoint['updated']=now
    return checkpoint['cache']
