#!/usr/bin/python
"""

Demo: get a list of this account's AMIs, in all regions

"""

import sys, time, os
sys.path += [ 'lib' ]
from boto_worker_pool import BotoWorkerPool
import boto.ec2

class MyPool(BotoWorkerPool):

    def get_regions(self):
        for region in boto.ec2.regions():
            self.enqueue(self.find_amis, region)

    def find_amis(self, region):
        conn = region.connect()
        [ self.resqueue.put((ami.id, ami.location)) for ami in
            conn.get_all_images(owners="self") ]

if __name__ == '__main__':
    pool = MyPool(workers=3, start_with="get_regions")
    for ami_id, image_location in pool.run():
        print ami_id, image_location



