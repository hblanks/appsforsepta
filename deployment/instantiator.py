#!/usr/bin/env python

"""
Usage: %prog [--key-name KEY_NAME] [--user-data USER_DATA_FILE] launch|teardown
"""

from optparse import OptionParser
import os
import sys
import time
import re

import boto

from extract_host_fingerprints import extract_host_fingerprints

########################## Options & constants #########################

parser = OptionParser(usage=__doc__.strip())
parser.add_option('--key-name', dest='key_name',
    help='EC2 key pair name to use. Else, we default to the first one we find.')
parser.add_option('--user-data', dest='user_data_path',
    help='user_data to use when creating an instance.')


AMI_ID = 'ami-e2af508b' # Ubuntu 11.04 instance boot
SECURITY_GROUP = 'hblanks-appsforsepta'
USER_DATA_PATH = os.path.join(os.path.dirname(__file__), 'user_data.sh')

############################### Functions ##############################

def read_user_data(path):
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data

def get_key_name(conn):
    return conn.get_all_key_pairs()[0].name

def get_or_create_security_group(conn):
    groups = [
        g for g in conn.get_all_security_groups() if g.name == SECURITY_GROUP]
    if groups:
        return groups[0]
    else:
        sg = conn.create_security_group(
            SECURITY_GROUP,
            'Temporary security group for web deployment options talk')
        for port in (22, 80):
            sg.authorize(ip_protocol='tcp',
                from_port=port, to_port=port, cidr_ip='0.0.0.0/0')
        return sg

def launch_instance(conn, key_name, user_data):
    return conn.run_instances(
        AMI_ID,
        key_name=key_name,
        min_count=1,
        max_count=1,
        instance_type='c1.medium',
        security_groups=[SECURITY_GROUP],
        user_data=user_data
        )

def wait_for_first_instance(reservation):
    instance = reservation.instances[0]
    while instance.state != 'running':
        print 'instance is %s' % reservation.instances[0].state
        time.sleep(15)
        instance.update()
    print 'instance up at %s' % instance.public_dns_name
    while True:
        output = instance.get_console_output().output
        if output:
            break
        print 'waiting on console output...'
        time.sleep(15)
    fingerprints = extract_host_fingerprints(output)
    if fingerprints:
        print 'host key fingerprints are:\n    %s' % (
            '\n    '.join(fingerprints)
            )

def list(conn):
    groups = [
        g for g in conn.get_all_security_groups() if g.name == SECURITY_GROUP]
    if groups:
        sg = groups[0]
        for instance in sg.instances():
            output = instance.get_console_output().output
            if output:
                fingerprints = extract_host_fingerprints(output)
                if fingerprints:
                    print instance.public_dns_name
                    print 'host key fingerprints are:\n    %s' % (
                        '\n    '.join(fingerprints)
                        )

def teardown(conn):
    groups = [
        g for g in conn.get_all_security_groups() if g.name == SECURITY_GROUP]
    if groups:
        sg = groups[0]
        for instance in sg.instances():
            print 'Terminating %s' % instance.id
            instance.terminate()
        while [i for i in sg.instances() if i.state != 'terminated']:
            time.sleep(15)
        conn.delete_security_group(SECURITY_GROUP)

############################## Main block ##############################

if __name__ == '__main__':
    options, args = parser.parse_args()
    if len(args) != 1 or args[0] not in ('launch', 'list', 'teardown'):
        parser.print_help()
        sys.exit(1)
    command = args[0]

    conn = boto.connect_ec2()
    if args[0] == 'launch':
        if options.user_data_path:
            user_data = read_user_data(options.user_data_path)
        else:
            user_data = None
        key_name = get_key_name(conn)
        get_or_create_security_group(conn)

        reservation = launch_instance(conn, key_name, user_data)
        wait_for_first_instance(reservation)
    elif args[0] == 'list':
        list(conn)
    else:
        teardown(conn)