# Copyright (C) 2013  ABRT Team
# Copyright (C) 2013  Red Hat, Inc.
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

import datetime

__all__ = ["daterange", "prev_days", "date_iterator"]


def daterange(a_date, b_date, step=1, desc=False):
    """
    Generator returning dates from lower to higher
    date if `desc` is False or from higher to lower
    if `desc` is True.

    `a_date` and `b_date` are always included in the
    result.
    """

    lower = min(a_date, b_date)
    higher = max(a_date, b_date)

    if desc:
        for x in range(0, (higher - lower).days, step):
            dt = higher - datetime.timedelta(x)
            yield dt

        yield lower
    else:
        for x in range(0, (higher - lower).days, step):
            dt = lower + datetime.timedelta(x)
            yield dt

        yield higher


def prev_days(num_days, start_from=None):
    """
    Return the list of dates preceding current day by `num_days`
    """

    dlist = []
    if not start_from:
        start_from = datetime.date.today()

    for i in range(1, num_days + 1):
        dlist.append(start_from - datetime.timedelta(days=i))

    return list(reversed(dlist))


def date_iterator(first_date, time_unit='d', end_date=None):
    '''
    Iterates from date until reaches end date or never finishes
    '''
    if time_unit == 'd':
        next_date_fn = lambda x: x + datetime.timedelta(days=1)
    elif time_unit == 'w':
        first_date -= datetime.timedelta(days=first_date.weekday())
        next_date_fn = lambda x: x + datetime.timedelta(weeks=1)
    elif time_unit == 'm' or time_unit == '*':
        first_date = first_date.replace(day=1)
        next_date_fn = lambda x: (x.replace(day=25) +
                                  datetime.timedelta(days=7)).replace(day=1)
    else:
        raise ValueError('Unknown time unit type : "%s"' % time_unit)

    toreturn = first_date
    yield toreturn
    while True:
        toreturn = next_date_fn(toreturn)
        if end_date is not None and toreturn > end_date:
            break

        yield toreturn
