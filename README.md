## OpenFIGI tickers extractor
1. (Optional, w/o it the process will take longer) Create a text file, where first line is OpenFIGI API key.
2. Run `python all_tickers.py`, with flags:
```
-a/--api_key_fp
a single path to a text file with OpenFIGI API key
```

```
-i/--input_fp
space separated paths to input JSON files (from previous runs), useful to extend some file with more info, or to merge multiple files into one
```
```
-o/--output_fp
a single path to output JSON file
```
```
-m/--mic_codes
space separated MIC codes of Financial Institutions, that provide ticker information
```
* [MIC codes options](https://www.openfigi.com/api/enumValues/v3/micCode)
* [MIC codes human-friendly table](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fwiki.edmcouncil.org%2Fdownload%2Fattachments%2F36339716%2Fexchange-code-mic-mapping.xls%3Fversion%3D1%26modificationDate%3D1560203343000%26api%3Dv2&wdOrigin=BROWSELINK)
```
-u/--unlisted
a flag to request unlisted stocks and derivatives as well
```
```
-b/--ban
space separated list of keywords (lowercase); securityType2 values containing those keywords will be ignored in retrieval process
```
```
--log_fp
a single path to store a log file
```
```
--start
an OpenFIGI API value that is expected by some requests, allowing retrieve data in pages (e.g. 5000 tickers may be split into 50 pages of 100 tickers, to get the next page, a "start" value from previous response has to be sent);
useful to continue an aborted process, such "start" value can be found in the log file
```
* [securityType2](https://www.openfigi.com/api/enumValues/v3/securityType2) variants

## Examples
```
python all_tickers.py -a openfigi_key.txt -o tickers_x.json -u -m RUSX SPIM XMOS XPIC XSAM XSIB

python all_tickers.py -a openfigi_key.txt -o tickers_misx.json -u -m MISX

python all_tickers.py -a openfigi_key.txt -o tickers_rtsx.json -u -m RTSX -b option future ingots sows cathode

python all_tickers.py -a openfigi_key.txt -i tickers_rtsx.json -o tickers_rtsx.json -u -m RTSX --start "..."

python all_tickers.py -a openfigi_key.txt -i tickers_rtsx.json tickers_x.json tickers_misx.json -o tickers.json -u

```