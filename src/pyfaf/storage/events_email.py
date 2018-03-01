# Copyright (C) 2018  ABRT Team
# Copyright (C) 2018  Red Hat, Inc.
#
# This file is part of faf.
#
# faf is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# faf is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with faf.  If not, see <http://www.gnu.org/licenses/>.

from . import Problem
from pyfaf.utils import web
from sqlalchemy import event
from pyfaf.common import log
from subprocess import Popen, PIPE
from email.mime.text import MIMEText


logger = log.getChildLogger(__name__)


@event.listens_for(Problem, 'after_insert')
def receive_after_insert(mapper, connection, target):
    """
    Send email notifications when new problem occurs.
    """
    try:
        components = ", ".join(target.components)
        txt = "New problem has occurred in {0}\n".format(components)
        txt += "Crash function: {0}\n".format(target.crash_function)
        txt += "URL: {0}\n".format(web.reverse("problems.item", problem_id=target.id))

        with open("/var/spool/faf/msg", "w") as f:
            f.write(txt)

        msg = MIMEText(txt)

        msg['From'] = "abrt@faf"
        msg['To'] = "mmarusak@redhat.com"  # what put here???
        msg['Subject'] = "New problem has occurred in {0}\n".format(components)

        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE, universal_newlines=True)
        p.communicate(msg.as_string())

    # Catch any exception. This is non-critical and mustn't break stuff
    # elsewhere.
    except Exception as e:
        logger.exception(e, exc_info=True)
