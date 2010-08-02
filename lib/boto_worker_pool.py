
import sys, os, time
from Queue import Queue, Empty
from threading import Thread, Lock
import boto.ec2

DEFAULT_NUMBER_OF_WORKERS = 3

class BotoWorkerPool:

    def __init__(self, workers=None, start_with=None):
        if workers is None:
            self.workers = len(self.regions()) + 1
        else:
            self.workers = DEFAULT_NUMBER_OF_WORKERS
        self.locks = [ ]
        self.threads = [ ]
        self.queue = Queue(0)
        self.resqueue = Queue(0)    # results queue

        if start_with is not None:
            self.enqueue(eval("self.%s" % start_with))

    def enqueue(self, *args):
        if len(args) == 1:
            self.queue.put(args[0])
        else:
            self.queue.put(args)

    def run(self):
        assert not self.queue.empty(), "run() called with empty queue"

        for i in range(self.workers):
            self.locks.append(Lock())
            self.threads.append(Thread(target=self.__worker, name=str(i),
                args=(self.locks[-1],)))
            self.threads[-1].start()

        while True:
            has_busy_thread = False
            for lock in self.locks:
                if lock.acquire(False):
                    lock.release()
                else:
                    has_busy_thread = True
                    break
            if not has_busy_thread and self.queue.empty():
                [ self.enqueue("exit") for i in range(self.workers) ]
                break
            else:
                time.sleep(0.5)

        for thread in self.threads: thread.join()

        self.results = [ ]
        while True:
            try: self.results.append(self.resqueue.get_nowait())
            except Empty: break
        return self.results

    def __worker(self, lock):
        while True:
            task = self.queue.get()
            if type(task) is str and task == "exit": break
            if callable(task):
                _callable, _args = task, ()
            else:
                _callable, _args = task[0], task[1:]

            lock.acquire()
            try:
                apply(_callable, _args)
            except Exception, e:
                # FIXME
                print e
            lock.release()

    def regions(self):
        return boto.ec2.regions()

