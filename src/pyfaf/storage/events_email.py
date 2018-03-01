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

from . import (Report, ReportContactEmail, ContactEmail, getDatabase,
               ReportPackage, ReportUnknownPackage, Problem, Package)
from pyfaf.utils import web
from sqlalchemy import event
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
from sqlalchemy import func

levels = tuple(2**n for n in range(2, 15))


def load_packages(problem_id):
    db = getDatabase()
    problem = db.session.query(Problem).filter(Problem.id == problem_id).first()

    report_ids = [report.id for report in problem.reports]

    sub = (db.session.query(ReportPackage.installed_package_id, func.sum(ReportPackage.count).label("cnt"))
                     .join(Report)
                     .filter(Report.id.in_(report_ids))
                     .filter(ReportPackage.type == 'CRASHED')
                     .group_by(ReportPackage.installed_package_id)
                     .subquery())

    packages_known = db.session.query(Package, sub.c.cnt).join(sub).all()
    packages_unknown = (db.session.query(ReportUnknownPackage, ReportUnknownPackage.count)
                                  .join(Report)
                                  .filter(ReportUnknownPackage.type == 'CRASHED')
                                  .filter(Report.id.in_(report_ids))).all()

    packages = packages_known + packages_unknown

    return sorted(list(set([x.nevr() for (x, y) in packages])))


@event.listens_for(Report.problem_id, "set")
def email_new_problem(target, value, oldvalue, initiator):
    """
    Send email notifications when new problem occurs.
    """
    try:
        # Only report when problem assigned for the first time
        if not oldvalue and value:
            # Only report if the problem was not already reported
            problem = target.problem
            packages = load_packages(problem.id)
            if problem.reports_count - target.count == 0:
                s = "New problem has occurred in {0}".format(target.component.name)
                txt = s + "\n"
                if (len(packages) == 1):
                    txt += "Affected package: {0}\n".format(packages[0])
                if (len(packages) >= 2):
                    txt += "Oldest affected package: {0}\n".format(packages[0])
                    txt += "Newest affected package: {0}\n".format(packages[-1])
                txt += "Crash function: {0}\n".format(target.crash_function)
                txt += "Error: {0}\n".format(target.errname)
                txt += "URL: {0}\n".format(web.reverse("problems.item", problem_id=value))
                if (len(packages) > 2):
                    txt += "All affected package:\n"
                    for pkg in packages:
                        txt += "    {0}\n".format(pkg)
                inform(s, txt, target)

    # Catch any exception. This is non-critical and mustn't break stuff
    # elsewhere.
    except:
        pass


@event.listens_for(Report.count, "set")
def email_multi_problem(target, value, oldvalue, initiator):
    try:
        if target.problem_id:
            problem = target.problem
            packages = load_packages(problem.id)
            for t in levels:
                if problem.reports_count - (value - oldvalue) < t and problem.reports_count >= t:
                    if problem.bugs:
                        s = "Problem in {0} with status {1} has occurred for {2}. time".format(target.component.name, problem.status, t)
                    else:
                        s = "Problem in {0} without bugzilla has occurred for {1}. time".format(target.component.name, t)
                    txt = s + "\n"
                    if (len(packages) == 1):
                        txt += "Affected package: {0}\n".format(packages[0])
                    if (len(packages) >= 2):
                        txt += "Oldest affected package: {0}\n".format(packages[0])
                        txt += "Newest affected package: {0}\n".format(packages[-1])
                    txt += "Crash function: {0}\n".format(target.crash_function)
                    txt += "Error: {0}\n".format(target.errname)
                    txt += "URL: {0}\n".format(web.reverse("problems.item", problem_id=problem.id))
                    if problem.bugs:
                        txt += "Bugs:\n"
                        for bug in problem.bugs:
                            txt += "    {0}\n".format(bug.url)
                    if (len(packages) > 2):
                        txt += "All affected package:\n"
                        for pkg in packages:
                            txt += "    {0}\n".format(pkg)
                    inform(s, txt, target)
    except:
        pass


def inform(s, txt, target):
    db = getDatabase()
    try:
        msg = MIMEText(txt)
        to = [email_address for (email_address, ) in
              (db.session.query(ContactEmail.email_address)
                         .join(ReportContactEmail)
                         .filter(ReportContactEmail.report == target))]

        msg['From'] = "abrt@faf"
        msg['To'] = to
        msg['Subject'] = "[FAF] " + s

        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE, universal_newlines=True)
        p.communicate(msg.as_string())
    except:
        pass
