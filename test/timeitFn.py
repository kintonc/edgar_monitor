def timeitFn():
    import timeit

    setup = """
from ../ciklist_lite import ciklist_lite
cikList = ciklist_lite()
cikList = [('0001163389','https://www.sec.gov/Archives/edgar/data/1163389/000172186820000557/0001721868-20-000557.txt')]

    """
    '''
    codeFull = """
from ../edgar1_old import filing
filing(cikList)
    """
    codeLite = """
from ../edgar1 import filingLite
filingLite(cikList)
    """'''

    codeCikList_old = """
from ../get_new_filings_cik_old import ciklist_old
ciklist_old()
    """

    codeCikListLite = """
from ../get_new_filings_cik import ciklist_lite
ciklist_lite()
    """



    number = 100

    # microseconds
    timeForAllRuns1 = timeit.timeit(stmt=codeCikListLite,number=number) #setup=setup
    timeForOneRun1 = timeForAllRuns1 / number  # in seconds

    # microseconds

    # microseconds
    timeForAllRuns2 = timeit.timeit(stmt=codeCikList_old,number = number)# setup=setup
    timeForOneRun2 = timeForAllRuns2 / number  # in seconds

    # microseconds
    print('Microseconds:')
    print('Lite/new: %d' % (timeForOneRun1 * 1000 * 1000))
    print('Full/old: %d' % (timeForOneRun2 * 1000 * 1000))

timeitFn()
