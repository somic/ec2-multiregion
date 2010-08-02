#!/usr/bin/python

import sys, os, time
sys.path += [ 'lib' ]
from boto_worker_pool import BotoWorkerPool

TOKEN = "__onesnapshot__"

class OneSnapshotPool(BotoWorkerPool):

    def get_regions(self):
        for region in self.regions():
            self.enqueue(self.find_eligible_volumes, region)

    def find_eligible_volumes(self, region):
        conn = region.connect()
        snapshots = conn.get_all_snapshots(owner="self")
        for snap in [ s for s in snapshots if s.description.find(TOKEN) >= 0 ]:
            self.enqueue(self.make_new_snapshot, region,
                         snap.volume_id, snap.id)

    def make_new_snapshot(self, region, volume, old_snapshot):
        conn = region.connect()
        snap = conn.create_snapshot(volume, "%d %s %s" % \
                 (int(time.time()), time.asctime(), TOKEN))
        if snap:
            self.enqueue(self.remove_old_snapshot, region, old_snapshot)

    def remove_old_snapshot(self, region, snapshot):
        conn = region.connect()
        conn.delete_snapshot(snapshot)

if __name__ == '__main__':
    OneSnapshotPool(start_with='get_regions').run()

