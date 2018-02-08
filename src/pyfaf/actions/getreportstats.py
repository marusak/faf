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

from operator import itemgetter
from pyfaf.storage import OpSysRelease, OpSysComponent, OpSys, Report
from pyfaf.queries import get_history_target
from sqlalchemy import func

from pyfaf.utils.date import date_iterator
from pyfaf.actions import Action
import datetime


class GetReportStats(Action):
    name = "getreportstats"

    def __init__(self):
        super(GetReportStats, self).__init__()

    def run(self, cmdline, db):
        # cmdline.since a cmdline.to
        # I guess that it is just fine from 1/1/2012
        since = datetime.date(2012, 1, 1)
        to = datetime.date.today()
        reports = self.get_reports(db, since, to)
        for release in reports:
            print release[0]
            print ",".join([str(x[1]) for x in release[1]])

    def tweak_cmdline_parser(self, parser):
        parser.add_argument("--since", action="store_true",
                            help="detailed view")
        parser.add_argument("--to", action="store_true",
                            help="detailed view")

    def get_reports(self, db, since, to):
        exclude_names = ['kernel']
        component_ids = map(itemgetter(0),
                            (db.session.query(OpSysComponent.id)
                                       .filter(~OpSysComponent.name.in_(exclude_names))
                                       .all()))

        reports = []

        resolution = 'd'

        hist_table, hist_field = get_history_target(resolution)

        opsysreleases = (db.session.query(OpSysRelease)
                         .join(OpSys)
                         .filter(OpSys.name == "Fedora")
                         .order_by(OpSysRelease.releasedate)
                         .all())

        for osr in opsysreleases:
            counts = (
                db.session.query(hist_field.label("time"),
                                 func.sum(hist_table.count).label("count"))
                .group_by(hist_field)
                .order_by(hist_field))

            counts = counts.filter(hist_table.opsysrelease_id == osr.id)

            # If we want to filter out component
            counts = (counts.join(Report)
                            .filter(Report.component_id.in_(component_ids)))

            counts = (counts.filter(hist_field >= since)
                            .filter(hist_field <= to))

            counts = counts.all()

            dates = set(date_iterator(since,
                                      resolution,
                                      to))

            for time, count in counts:
                dates.remove(time)
            for date in dates:
                counts.append((date, 0))
            counts = sorted(counts, key=itemgetter(0))
            reports.append((str(osr), counts))

        return reports
