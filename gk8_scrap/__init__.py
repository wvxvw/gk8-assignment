# -*- coding: utf-8 -*-

import queue
import time
import logging
import json

from argparse import ArgumentParser
from multiprocessing import Process, Queue, Event

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


# TODO(wvxvw): Also configure logging
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
parser.add_argument(
    '-v',
    '--verbosity',
    default=logging.WARNING,
    type=int,
    help='''
    Logging verbosity level. Default 30 (WARNING).
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

    def process_url(self, url):
        logging.info('Processing: {}'.format(url))
        src_tx = url.split('/')[-1]
        self.driver.get(url)
        txs = self.find_all_transactions()
        logging.info('Found {} transactions'.format(len(txs)))
        if not txs:
            self.sink.put((src_tx, 'coinbase'))
        else:
            for tx in txs:
                self.sink.put((src_tx, tx))

    def find_all_transactions(self):
        tx_path = (
            '//*[@id="__next"]/div[3]/div/div[3]/div/div[3]/'
            'div[2]/div[1]/div[2]/div/div[1]/div/div/a'
        )
        return [
            a.get_attribute('href').split('/')[-1]
            for a in self.driver.find_elements_by_xpath(tx_path)
        ]


def all_paths_found(paths):
    if not paths:
        return False
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


def find_first_tx(node_url, page_url):
    driver = webdriver.Remote(
        command_executor=node_url,
        desired_capabilities=DesiredCapabilities.CHROME,
    )
    driver.get(page_url)
    # This site seriously doesn't want to be scraped
    tx_path = (
        '//*[@id="__next"]/div[3]/div/div[5]/div/div[2]'
        '/div[2]/div/div[2]/div/div[2]/div[1]/div[2]/a'
    )
    return driver.find_elements_by_xpath(tx_path)[0].text


def scrap(argsv):
    pargs = parser.parse_args(argsv)

    logging.basicConfig(
        force=True,
        level=pargs.verbosity,
    )

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

    try:
        tx = find_first_tx(workers[0].node, pargs.url)
        paths = {tx: {}}
        jobs.put_nowait(tx)
        
        while not all_paths_found(paths):
            try:
                src_tx, tx = sink.get()
                update_path(paths, src_tx, tx)
                jobs.put_nowait(tx)
            except queue.Empty:
                time.sleep(1)

        is_done.set()
        
        if not pargs.output:
            print(json.dumps(paths, indent=4))
        else:
            with open(pargs.output, 'w') as f:
                json.dump(paths, f, indent=4)
    finally:
        for worker in workers:
            worker.terminate()


def main(argsv):
    try:
        scrap(argsv)
    # TODO(wvxvw): This needs to be more specific about errors
    except Exception as e:
        logging.exception(e)
        return 1
    return 0
