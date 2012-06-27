__author__ = 'tommi'

from subprocess import Popen, PIPE
from datetime import datetime

def gitlog(nagiosdir):
    """
    Executed git log and returns a array of recent changes in order newest to oldest
    """
    fh = Popen(["git", "log" ,"-5", "--pretty=%an:%ae:%at:%s"], cwd=nagiosdir, stdin=None, stdout=PIPE )

    gitstring = fh.communicate()[0]

    result = []
    for logline in gitstring.splitlines():
        author, authoremail, authortime, comment = logline.split(":", 3)
        result.append( {
            "author": author,
            "authoremail": authoremail,
            "authortime": datetime.fromtimestamp(float(authortime)),
            "comment": comment,
        })
    return result