# -*- coding: utf-8 -*-

import queue
import time

from argparse import ArgumentParser
from multiprocessing import Process, Queue, Event

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


parser = ArgumentParser('GK8 blockchain.com scrapper')
parser.add_argument(
    '-o',
    '--output',
    default=None,
    help='''
    Store scrapper's output in this file (default: stdout)
    ''',
)
parser.add_argument(
    '-u',
    '--url',
    required=True,
    help='''
    URL of the blockchain.com to start from
    ''',
)
parser.add_argument(
    '-n',
    '--node',
    action='append',
    default=[],
    help='''
    Selenium worker node URL
    ''',
)


def tx_to_url(tx):
    return 'https://www.blockchain.com/btc/tx/{}'.format(tx)


class WebDriverProcess(Process):

    def __init__(self, node, sink, jobs, is_done, timeout=1):
        super().__init__()
        self.node = node
        self.sink = sink
        self.jobs = jobs
        self.is_done = is_done
        self.timeout = timeout

    def run(self):
        self.driver = webdriver.Remote(
            command_executor=self.node,
            desired_capabilities=DesiredCapabilities.CHROME,
        )
        while not self.is_done.is_set():
            try:
                tx = self.jobs.get_nowait()
                self.process_url(tx_to_url(tx))
            except queue.Empty:
                time.sleep(self.timeout)

    def process_url(self, url, src_tx):
        self.driver.get(url)
        txs = self.find_all_transactions()
        if not txs:
            self.sink.put((src_tx, 'coinbase'))
        else:
            for tx in txs:
                self.sink.put((src_tx, tx))

    def find_all_transactions(self):
        pass


def all_paths_found(paths):
    if paths == 'coinbase':
        return True

    for k, v in paths.items():
        if not v:
            return False
        if isinstance(v, dict):
            for sk, sv in v.items():
                if not all_paths_found(sv):
                    return False

    return True


def update_path(paths, src_tx, tx):
    for k, v in paths.items():
        if k == src_tx:
            if tx == 'coinbase':
                paths[k] = tx
            else:
                v[tx] = {}
            break
        elif isinstance(v, dict):
            update_path(v, src_tx, tx)


def main(argsv):
    pargs = parser.parse_args(argsv)
    sink = Queue()
    jobs = Queue()
    is_done = Event()
    workers = [
        WebDriverProcess(
            'http://{}:5555/wd/hub'.format(node),
            sink,
            jobs,
            is_done,
        )
        for node in pargs.node
    ]

    for worker in workers:
        worker.start()

    tx = find_first_tx(pargs.node[0], pargs.url)
    paths = {tx: {}}
    self.jobs.put_nowait(tx)

    while not all_paths_found(paths):
        try:
            src_tx, tx = sink.get()
            update_path(paths, src_tx, tx)
            jobs.put_nowait(tx)
        except queue.Empty:
            time.sleep(1)
