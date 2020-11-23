# edgar_monitor

Some scripts to monitor the SEC's EDGAR system for the latest 10-K and 10-Q filings, and retrieve revenue + net income + EPS numbers from 10-K and 10-Q.

Scripts are written with speed performance in mind, in order to get 10-K and 10-Q as soon as they are released. Currently, scripts take ~100 ms to check for new filings.

Uses [farhadab's sec-edgar-financials library](https://github.com/farhadab/sec-edgar-financials), but I made some speed performance improvements to it, to reduce loading time by 50-80%.