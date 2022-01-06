import requests
import sys
import time
from pathlib import Path
import json
import argparse
import tqdm

LIMIT_REACHED_CODE = 429
SUCCESS_CODE = 200
DUMP_EVERY_N_ENTRIES = 800
URL = 'https://api.openfigi.com/v3/filter/'
HEADERS = {'Content-Type': 'text/json'}
# MIC_CODES = ['MISX', 'RTSX', 'RUSX', 'SPIM', 'XMOS', 'XPIC', 'XSAM', 'XSIB']
# EXCHANGE_CODES = ['RX', 'RN', 'RP', 'RR', 'RT']
LIMIT_COOLDOWN_SEC = 16

def log(tag, message, file=None):
    tqdm.tqdm.write(f"{tag} {message}", file=file)
    if file is not None:
        file.flush()

def save_tickers(fp, tickers_list):
    mem = set()
    no_dup = []
    for e in tickers_list:
        if isinstance(e['ticker'], str) and e['ticker'] not in mem:
            mem.add(e['ticker'])
            no_dup.append(e)
    no_dup.sort(key=lambda e: e['ticker'])
    log("INFO", f"Dumping {len(no_dup)} entries to {fp}")
    with open(fp, 'w') as f:
        json.dump(no_dup, f)

def get_api_key(api_key_file):
    try:
        with open(api_key_file, 'r') as f:
            return f.readline()
    except:
        return None

def request_security_variants(banned_security):
    response = requests.get(url='https://api.openfigi.com/v3/mapping/values/securityType2',
        headers={'Content-Type': 'application/json'})
    assert response.status_code == SUCCESS_CODE, f"Failed request {response.status_code}"
    return list(filter(lambda v: not any([banned in v.lower() for banned in banned_security]), 
        response.json()['values']))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--api_key_fp", type=str, default=None)
    parser.add_argument("-i", "--input_fp", type=str, nargs="+", default=None)
    parser.add_argument("-o", "--output_fp", type=str, default="tickers.json")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--mic_codes", nargs="+", default=[])
    group.add_argument("-e", "--exchange_codes", nargs="+", default=[])
    parser.add_argument("-u", "--unlisted", action='store_true')
    parser.add_argument("-b", "--ban", nargs="+", default=[])
    parser.add_argument("--log_fp", type=str, default="log.txt")
    parser.add_argument("--start", type=str, default=None)
    return parser.parse_args()

def get_response(header, exchange_code=None, mic_code=None, security=None, start=None, limit_callback=None, include_unlisted=False):
    request = {}
    if include_unlisted:
        request['includeUnlistedEquities'] = True
    if exchange_code is not None:
        request['exchCode'] = exchange_code
    if mic_code is not None:
        request['micCode'] = mic_code
    if security is not None:
        request['securityType2'] = security
    if start is not None:
        request['start'] = start

    while True:
        response = requests.post(url=URL, headers=header, json=request)

        if response.status_code == LIMIT_REACHED_CODE:
            if limit_callback is not None:
                limit_callback()
            time.sleep(LIMIT_COOLDOWN_SEC)
        elif response.status_code == SUCCESS_CODE:
            return response.json()

def main():
    args = parse_args()
    api_key = get_api_key(args.api_key_fp)
    if api_key is not None:
        HEADERS['X-OPENFIGI-APIKEY'] = api_key
    log("INFO", f"ARGS {args}")

    if args.input_fp is not None:
        all_tickers = []
        for fp in args.input_fp:
            log("INFO",f"Reading input {fp}")
            with open(fp, 'r') as f:
                all_tickers.extend(json.load(f))
    else:
        all_tickers = []

    if len(args.mic_codes) == 0 and len(args.exchange_codes) == 0:
        save_tickers(args.output_fp, all_tickers)
        return

    log_file = None
    if args.log_fp is not None:
        log_file = open(args.log_fp, 'a')

    if args.ban != []:
        security_variants = request_security_variants(banned_security=args.ban)
    else:
        security_variants = [None]
    start = args.start
    tqdm_bar = tqdm.trange(len(args.mic_codes)*len(security_variants), leave=True)
    use_exchange_codes = args.exchange_codes != []
    codes_iter = args.exchange_codes if use_exchange_codes else args.mic_codes
    for code in codes_iter:
        if use_exchange_codes:
            exchange_code = code
            mic_code = None
        else:
            mic_code = code
            exchange_code = None
        for security in security_variants:
            n_added = 0
            while True:
                sys.stderr.flush()
                response = get_response(HEADERS, mic_code=mic_code, exchange_code=exchange_code,
                    security=security, include_unlisted=args.unlisted, start=start,
                    limit_callback=lambda: log("INFO", f"Limit reached, waiting {LIMIT_COOLDOWN_SEC} sec"))
                if 'error' in response.keys():
                    log("ERR", response['error'])
                    return

                do_dump = len(all_tickers) // DUMP_EVERY_N_ENTRIES != (len(all_tickers) + len(response['data'])) // DUMP_EVERY_N_ENTRIES

                all_tickers.extend(response['data'])
                n_added += len(response['data'])
                n_total = response['total'] if 'total' in response.keys() else -1
                log("INFO", f"{code}|{security}|{len(response['data'])}|{n_added}/{n_total}")

                if do_dump: # checkpoint
                    save_tickers(args.output_fp, all_tickers)

                if 'next' not in response.keys():
                    break

                start = response['next']
                time.sleep(1.0)
                log("INFO", f"{code}|{security}|{n_added}/{n_total}|{start}", file=log_file)

            start = None
            tqdm_bar.update()

    save_tickers(args.output_fp, all_tickers)

    if log_file is not None:
        log_file.flush()
        log_file.close()

if __name__ == "__main__":
    main()