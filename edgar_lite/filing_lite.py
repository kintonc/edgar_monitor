'''
Logic related to the handling of filings and documents
'''
from edgar.requests_wrapper import GetRequest
from edgar.document import Document
from edgar.sgml import Sgml
from edgar.dtd import DTD
from edgar.financials_lite import get_financial_report_lite
from datetime import datetime
from fuzzywuzzy import process, fuzz
from pprint import pprint


FILING_SUMMARY_FILE = 'FilingSummary.xml'

class Statements:
    # used in parsing financial data; these are the statements we'll be parsing
    # To resolve "could not find anything for ShortName..." error, likely need
    # to add the appropriate ShortName from the FilingSummary.xml here.
    income_statements = ['consolidated statements of income',
                    'consolidated statements of operations',
                    'consolidated statement of earnings',
                    'condensed consolidated statements of income (unaudited)',
                    'condensed consolidated statements of income',
                    'condensed consolidated statements of operations (unaudited)',
                    'condensed consolidated statements of operations',
                    'condensed consolidated statement of earnings (unaudited)',
                    'condensed consolidated statement of earnings',
                    'condensed consolidated statements of earnings',
                    'condensed consolidated statements of earnings (unaudited)',
                    'condensed statements of income',
                    'condensed statements of operations',
                    'condensed statements of operations (unaudited)',
                    'condensed statements of operations and comprehensive loss',
                    'condensed consolidated income statements (unaudited)',
                    'condensed consolidated income statements',
                    'condensed consolidated statements of comprehensive loss (unaudited)',
                    'consolidated statements of operations and comprehensive income / (loss) (unaudited)',
                    'consolidated statement of income (unaudited)',
                    'consolidated statements of income (unaudited)',
                    'consolidated statement of income',
                    'condensed consolidated statements of comprehensive income (unaudited)',
                    'consolidated statements of operations (unaudited)',
                    'interim consolidated statements of operations (unaudited)',
                    'interim consolidated statements of operations',
                    'unaudited consolidated statements of operations',
                    'unaudited consolidated statement of operations',
                    'unaudited condensed consolidated statements of operations and comprehensive income( loss)',
                    'unaudited condensed consolidated statements of operations and comprehensive income (loss)',
                    'consolidated and combined statements of operations',
                    'consolidated and combined statements of operation',
                    'consolidated and combined statement of operations',
                    'consolidated and combined statement of operations',
                         ]
    balance_sheets = ['consolidated balance sheets',
                    'consolidated statement of financial position',
                    'condensed consolidated statement of financial position (current period unaudited)',
                    'condensed consolidated statement of financial position (unaudited)',
                    'condensed consolidated statement of financial position',
                    'condensed consolidated balance sheets (current period unaudited)',
                    'condensed consolidated balance sheets (unaudited)',
                    'condensed consolidated balance sheets',
                    'condensed balance sheets',
                    'Consolidated Balance Sheet (Unaudited)',
                    ]
    cash_flows = ['consolidated statements of cash flows',
                    'condensed consolidated statements of cash flows (unaudited)',
                    'condensed consolidated statements of cash flows',
                    'condensed statements of cash flows'
                    ]

    all_statements = income_statements + balance_sheets + cash_flows


class Filing_lite:

    STATEMENTS = Statements()
    sgml = None

    def __init__(self, url, company=None):
        self.fuzzy = False
        self.url = url
        # made this company instead of symbol since not all edgar companies are publicly traded
        self.company = company

        # {filename:Document}
        self.documents = {}
        self.documents_lite = {}

    def get_filing_summary_lite(self):
        import edgar.sgml

        url = self.url + "/" + FILING_SUMMARY_FILE
        print('Processing ' + FILING_SUMMARY_FILE)

        import requests
        import xmltodict
        self.documents_lite[FILING_SUMMARY_FILE] = xmltodict.parse(requests.get(url).text)

    def _get_financial_data_lite(self, statement_short_names, get_all):
        '''
        Returns financial data used for processing 10-Q and 10-K documents
        '''
        financial_data = []

        # if a FilingSummary.xml file does not exist... return False
        if 'FilingSummary' not in self.documents_lite[FILING_SUMMARY_FILE]:
            print('No Filing Summary exists')
            return False

        filingSummaryReports = self.documents_lite[FILING_SUMMARY_FILE]['FilingSummary']['MyReports']['Report']
        #pprint(len(filingSummaryReports))
        #pprint(filingSummaryReports[0]['ShortName'])

        statementCounter = 0
        statement_list = self._get_statement_lite(statement_short_names)

        for statement in statement_list:
            statementCounter += 1
            short_name = statement[0]
            filename = statement[1]

            for report in filingSummaryReports:
                if short_name == report['ShortName'].lower():
                    url = self.url + '/' + filename
                    #print(url)
                    response = GetRequest(url).response
                    #print(response)
                    text = response.text

                    dtd = DTD()
                    sgml = Sgml(text, dtd)
                    self.sgml = sgml

                    import json
                    sgmlString = json.dumps(sgml.map)
                    sgmlString = sgmlString[16:]
                    sgmlString = sgmlString[:-2]
                    sgml.map = json.loads(sgmlString)

                    self.documents[filename] = Document(sgml.map)

                    financial_html_text = self.documents[filename].doc_text.data

                    financial_report = get_financial_report_lite(self.company, financial_html_text)
                    # if get_financial_report_lite has an error, it will return as False
                    # return as False again, pass it up the stack
                    if financial_report == False and statementCounter == len(statement_list):
                        return False
                    elif  financial_report == False and statementCounter != len(statement_list):
                        continue

                    if get_all:
                        financial_data.append(financial_report)
                    else:
                        return financial_report

        return financial_data


    def _get_statement_lite(self, statement_short_names):
        '''
        Return a list of tuples of (short_names, filenames) for
        statement_short_names in filing_summary_xml
        '''
        statement_names = []

        if FILING_SUMMARY_FILE in self.documents_lite:
            filing_summary_reports_dict = self.documents_lite[FILING_SUMMARY_FILE]['FilingSummary']['MyReports']['Report']

            for short_name in statement_short_names:
                filename = self.get_html_file_name_lite(filing_summary_reports_dict, short_name)
                if filename is not None:
                    statement_names += [(short_name, filename)]

            if len(statement_names) == 0:
                statement_names= self.get_html_file_name_fuzzy_lite(filing_summary_reports_dict, 'income statement')


        else:
            print('No financial documents in this filing')

        if statement_names is None:
            statement_names = []
            print('No financial documents could be found. Likely need to \
            update constants in edgar.filing.Statements.')
        elif len(statement_names) == 0:
            print('No financial documents could be found. Likely need to \
            update constants in edgar.filing.Statements.')
        #print(statement_names)
        return statement_names

    @staticmethod
    def get_html_file_name_lite(filing_summary_reports_dict, report_short_name):
        '''
        Return the HtmlFileName (FILENAME) of the Report in FilingSummary.xml
        (filing_summary_xml) with ShortName in lowercase matching report_short_name
        e.g.
             report_short_name of consolidated statements of income matches
             CONSOLIDATED STATEMENTS OF INCOME
        '''
        for report in filing_summary_reports_dict:
            short_name = report['ShortName']
            if short_name is None:
                print('The following report has no ShortName element')
                #print(report)
                continue
            # otherwise, get the text and keep procesing
            short_name = short_name.lower()
            # we want to make sure it matches, up until the end of the text
            if short_name == report_short_name.lower():
                filename = report['HtmlFileName']
                return filename
        #print(f'could not find anything for ShortName {report_short_name.lower()}')
        return None

    def get_html_file_name_fuzzy_lite(self, filing_summary_reports_dict, report_short_name_match):
        '''
        Return a list of HtmlFileName (FILENAME) of the Report in FilingSummary.xml
        (filing_summary_reports_dict) whose ShortName is similar to report_short_name_match
        e.g.
             report_short_name of consolidated statements of income matches
             CONSOLIDATED STATEMENTS OF INCOME
        '''

        self.fuzzy = True
        print('Fuzzy Start: "get_html_file_name_fuzzy_lite"')

        short_names_list = []
        for report in filing_summary_reports_dict:
            if 'MenuCategory' in report:
                if report['MenuCategory'] == 'Statements':
                    short_name = report['ShortName']
                    if short_name is None:
                        print('The following report has no ShortName element')
                        #print(report)
                        continue
                    # otherwise, get the text and keep procesing
                    short_name = short_name.lower()
                    short_names_list.append(short_name)

        # Do a fuzzy match, match "report_short_name_match to a list of short name candidates (short_name_list)
        matchRatios = process.extract(report_short_name_match,short_names_list)
        # Exclude any reports whose short name contains words/terms in exclude_list
        exclude_list = ['deficit', 'Deficit']
        matchRatios = [x for x in matchRatios if not any(exclude in x[0] for exclude in exclude_list)]
        # Sort by descending order of similarity
        matchRatios.sort(key = lambda x: x[1], reverse=True)
        print(matchRatios)

        statement_names = []

        # Create a list of report_name, filename pairs to return
        for matchTuple in matchRatios:
            report_name = matchTuple[0].lower()
            for report in filing_summary_reports_dict:
                short_name = report['ShortName']

                if report_name == short_name.lower():
                    filename = report['HtmlFileName']
                    statement_names.append((report_name, filename))

        if len(statement_names) == 0:
            print(f'could not find anything for ShortName {report_short_name_match.lower()}')
            return None
        #print(statement_names)
        return statement_names

    # Returns a FinancialReport_Lite object.
    def get_income_statements_lite(self):
        return self._get_financial_data_lite(self.STATEMENTS.income_statements, False)

    '''
    def get_balance_sheets(self):
        return self._get_financial_data(self.STATEMENTS.balance_sheets, False)

    def get_cash_flows(self):
        return self._get_financial_data(self.STATEMENTS.cash_flows, False)'''