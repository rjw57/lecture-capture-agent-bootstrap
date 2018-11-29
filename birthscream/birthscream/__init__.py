"""
Scream one's existence into the void.

Usage:
    birthscream (-h | --help)
    birthscream [--verbose] [--no-output] [--post-url=URL]

Options:

    -h, --help                  Show a brief usage summary.
    -v, --verbose               Increase logging verobsity.
    -q, --no-output             Do not output payload to standard output.
    --post-url=URL              Post payload to the specified URL.

Birthscream gathers various pieces of system information into a single JSON payload and either
displays it in standard output and/or HTTP POSTs it to a given URL.

"""
import json
import logging
import random
import socket
import sys

import docopt
import netifaces
import requests
import wifi


LOG = logging.getLogger(__name__)


# Keys from wifi.Cell which should be output in payload.
CELL_KEYS = (
    'ssid signal quality frequency bitrates encrypted channel address mode encryption_type'.split()
)

# Lightly edited list of sites from Alexa top 500 which we use as examples of site we "should" be
# able to get to if connectivity to the general Internet is possible.
#
# https://www.alexa.com/topsites
EXTERNAL_CONNECTIVITY_URLS = [
    'https://google.com/',
    'https://youtube.com/',
    'https://facebook.com/',
    'https://wikipedia.org/',
    'https://yahoo.com/',
    'https://twitter.com/',
]


# Default configuration which may be overridden from  external config.
DEFAULT_CONFIGURATION = {
    'dump_to_stdout': True,
    'post_url': None,
}


def main():
    opts = docopt.docopt(__doc__)

    logging.basicConfig(
        level=logging.INFO if opts['--verbose'] else logging.WARN,
        format='%(levelname)s: %(message)s'
    )

    LOG.info('Gathering system information')

    payload = {
        'hostname': socket.gethostname(),
        'fullyQualifiedDomainName': socket.getfqdn(),
        'externalConnectivity': external_connectivity_test(),
        'networkInterfaces': get_network_interfaces(),
    }

    if not opts['--no-output']:
        LOG.info('Dumping payload to standard output')
        json.dump(payload, sys.stdout, indent=2)

    if opts['--post-url'] is not None:
        LOG.info('POST-ing payload to "%s"', opts['--post-url'])
        try:
            response = requests.post(opts['--post-url'], json=payload)
            response.raise_for_status()
        except Exception as e:
            LOG.error('Exception when POST-ing payload')
            LOG.exception(e)
        LOG.info('Payload successfully POST-ed')


def get_network_interfaces():
    return [
        {
            'name': interface,
            'internetAddresses': netifaces.ifaddresses(interface).get(netifaces.AF_INET, []),
            'linkAddresses': netifaces.ifaddresses(interface).get(netifaces.AF_LINK, []),
            'wifiNetworks': get_wifi_networks(interface),
        }
        for interface in netifaces.interfaces()
    ]


def get_wifi_networks(interface):
    networks = []

    try:
        networks = [
            {k: getattr(cell, k) for k in CELL_KEYS}
            for cell in wifi.Cell.all(interface)
        ]
    except wifi.exceptions.InterfaceError:
        # The InterfaceError implies that the interface does not support wifi scanning and is
        # innocuous.
        pass
    except Exception as e:
        # Any other error should be logged
        LOG.error('Failure to scan wifi network')
        LOG.exception(e)

    return networks


def external_connectivity_test():
    test_url = random.choice(EXTERNAL_CONNECTIVITY_URLS)
    timeout = 5
    elapsed_seconds = None
    status_code = None

    try:
        response = requests.get(test_url, timeout=5)
        elapsed_seconds = response.elapsed.total_seconds()
        status_code = response.status_code

        # We still succeed even if the status code fails since some site may try to return error
        # codes to bots and we care that we got *some* response.
        succeeded = True
    except Exception:
        succeeded = False

    return {
        'succeeded': succeeded, 'url': test_url, 'timeout': timeout,
        'statusCode': status_code, 'elapsedSeconds': elapsed_seconds,
    }


if __name__ == '__main__':
    main()
