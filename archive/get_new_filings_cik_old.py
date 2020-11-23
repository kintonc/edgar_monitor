def ciklist_old():
    # this uses FeedParser to get latest SEC filings
    # Feedparser is a slow library, therefore we no longer use it
    import re
    import feedparser
    link_10q = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-q&company=&dateb=&owner=include&start=0&count=40&output=atom'

    feed = feedparser.parse(link_10q)
    #print(feed)
    #print(type(feed))
    entries = feed['entries']

    cikList = []

    for i in range(0, len(entries)):
        cik = re.findall('\d\d\d\d\d\d\d\d\d\d', entries[i]['title'])[0]
        url = entries[i]['link']
        url = url.replace('-index.htm', '.txt')
        cikList.append((cik, url))

    return cikList

def filing(cikList):
    # This is inspired from examples
    # This uses the full version of the library, not the lite version, therefore not using it
    from edgar.stock import Stock
    import datetime

    tickers = []

    '''with open('../data/spy500 - test.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            tickers.append(row[0])'''

    tickers = ['XYL']
    print(tickers)

    for tuple in cikList:
        print('********************************')
        print('CIK: %s' % tuple[0])
        print('URL: %s' % tuple[1])

        try:
            # stock = Stock(ticker)
            stock = Stock(cik=tuple[0].lstrip('0'))
        except IndexError as e:
            print(e)
            continue

        period = 'quarterly'  # or 'annual', which is the default
        year = 0  # can use default of 0 to get the latest
        quarter = 0  # 1, 2, 3, 4, or default value of 0 to get the latest
        # using defaults to get the latest annual, can simplify to stock.get_filing()

        # Get CIK from .csv, get 10-K / 10-Q / file link from master.idx lookup, process .txt
        try:
            filing = stock.get_filing(period, year, quarter, filing_url=tuple[1])
        except Exception as e:
            print(e)
            continue

        # financial reports (contain data for multiple years)
        try:
            income_statements = filing.get_income_statements()
        except Exception as e:
            print(e)
            if str(e) == 'list index out of range':
                continue

        # balance_sheets = filing.get_balance_sheets()
        # cash_flows = filing.get_cash_flows()

        labelDict = {
            'revenue': ['us-gaap_RevenueFromContractWithCustomerExcludingAssessedTax',
                        'us-gaap_RevenueFromContractWithCustomerIncludingAssessedTax',
                        'us-gaap_Revenues'],
            'netIncome': ['us-gaap_NetIncomeLoss',
                          'us-gaap_NetIncomeLossAvailableToCommonStockholdersBasicAbstract',
                          'us-gaap_NetIncomeLossAvailableToCommonStockholdersBasic',
                          ''
                          ],
            'epsBasic': ['us-gaap_EarningsPerShareBasic',
                         'us-gaap_EarningsPerShareBasicAndDiluted',
                         'us-gaap_IncomeLossFromContinuingOperationsPerBasicShare'],
            'epsDiluted': ['us-gaap_EarningsPerShareDiluted',
                           'us-gaap_EarningsPerShareBasicAndDiluted',
                           'us-gaap_IncomeLossFromContinuingOperationsPerDilutedShare']
        }

        for key in labelDict:
            for label in labelDict[key][:]:
                if label not in income_statements.reports[0].map and ('defref_' + label) not in \
                        income_statements.reports[
                            0].map:
                    labelDict[key].remove(label)

        for report in income_statements.reports:
            print(report.date)
            print("Last %d months" % report.months)

            for key in labelDict:
                print(key + ':')
                for label in labelDict[key]:
                    print(label)
                    try:
                        print(report.map[label])
                    except KeyError as e:
                        print(e)
                        continue
