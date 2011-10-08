#!/usr/bin/env python

"""
Simple library for getting fingerprints out of console output.
"""

import re

FINGERPRINT_BLOCK_PAT = re.compile(
    (
        '-----BEGIN SSH HOST KEY FINGERPRINTS-----'
        '(.*)'
        '-----END SSH HOST KEY FINGERPRINTS-----'
    ), re.MULTILINE | re.DOTALL
    )
FINGERPRINT_PAT = re.compile('^.* \d+ ([0-9a-f:]+) .*\.pub', re.MULTILINE)

def extract_host_fingerprints(console_output):
    """
    Extracts fingerprints from a string of EC2 console output.

    Example::

        >>> s = '''
        ... ec2:
        ... ec2: #############################################################
        ... ec2: -----BEGIN SSH HOST KEY FINGERPRINTS-----
        ... ec2: 2048 f1:40:a7:4e:0f:28:8d:12:21:59:f1:ff:03:5f:63:54 /etc/ssh/ssh_host_rsa_key.pub (RSA)
        ... ec2: 1024 28:f3:ef:a6:86:05:50:33:76:16:24:32:56:14:06:13 /etc/ssh/ssh_host_dsa_key.pub (DSA)
        ... ec2: -----END SSH HOST KEY FINGERPRINTS-----
        ... ec2: #############################################################
        ... '''
        >>> extract_host_fingerprints(s)
        ['f1:40:a7:4e:0f:28:8d:12:21:59:f1:ff:03:5f:63:54',
         '28:f3:ef:a6:86:05:50:33:76:16:24:32:56:14:06:13']
    """

    match = FINGERPRINT_BLOCK_PAT.search(console_output)
    if match:
        return list(set(
            m.group(1) for m in FINGERPRINT_PAT.finditer(match.group(1))
            ))

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
