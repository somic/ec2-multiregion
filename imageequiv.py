#!/usr/bin/python
"""

imageequiv.py takes AMI ID, kernel ID or ramdisk ID and
finds equivalent IDs in all regions, based on matching name
or manifest file location

"""

import sys, time, os
sys.path += [ 'lib' ]
from boto_worker_pool import BotoWorkerPool
import boto.exception

class MyPool(BotoWorkerPool):

    def get_regions(self):
        for region in self.regions():
            self.enqueue(self.find_base_ami, region)

    def find_base_ami(self, region):
        conn = region.connect()
        try:
            for region in self.regions():
                self.enqueue(self.find_ami, region,
                               conn.get_image(self.base_image))
        except boto.exception.EC2ResponseError:
            pass

    def find_ami(self, region, base_ami):
        for ami in region.connect().get_all_images():
            if ami.ownerId == base_ami.ownerId:
                if ami.name == base_ami.name or \
                    ami.location == base_ami.location:
                        self.resqueue.put(ami)
                        return
                    
if __name__ == '__main__':
    pool = MyPool(start_with="get_regions")
    try:
        pool.base_image = sys.argv[1]
    except IndexError:
        print 'Usage: %s ami_id|aki_id|ari_id' % sys.argv[0]
        sys.exit(1)

    res = pool.run()
    if len(res) == 0:
        print 'Not found'
        sys.exit(1)
    else:
        for ami in res:
            print ami.id, ami.region.name, ami.name, ami.location



