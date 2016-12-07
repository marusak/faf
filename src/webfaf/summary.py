from operator import itemgetter
from pyfaf.storage import (Report,
                           OpSysRelease)
from pyfaf.queries import get_history_target
from flask import Blueprint, render_template, request
from sqlalchemy import func


summary = Blueprint("summary", __name__)

from webfaf_main import db, flask_cache
from forms import SummaryForm, component_names_to_ids
from utils import date_iterator
from reports import get_reports
from utils import Pagination

def index_plot_data_cache(filter_form):
    key = filter_form.caching_key()

    cached = flask_cache.get(key)
    if cached is not None:
        return cached

    reports = []

    pg = Pagination(request)
    all_reports = get_reports(filter_form, pg)
    all_reports_ids = [report.id for report in all_reports]

    hist_table, hist_field = get_history_target(
        filter_form.resolution.data)

    (since_date, to_date) = filter_form.daterange.data

    if filter_form.opsysreleases.data:
        opsysreleases = filter_form.opsysreleases.data
    else:
        opsysreleases = (
            db.session.query(OpSysRelease)
            .filter(OpSysRelease.status != "EOL")
            .order_by(OpSysRelease.releasedate)
            .all())

    for osr in opsysreleases:
        counts = (
            db.session.query(hist_field.label("time"),
                             func.sum(hist_table.count).label("count"))
            .group_by(hist_field)
            .order_by(hist_field))

        counts = counts.filter(hist_table.opsysrelease_id == osr.id)

        counts = (counts.join(Report)
                        .filter(Report.id.in_(all_reports_ids)))

        counts = (counts.filter(hist_field >= since_date)
                        .filter(hist_field <= to_date))

        counts = counts.all()

        dates = set(date_iterator(since_date,
                                  filter_form.resolution.data,
                                  to_date))

        for time, count in counts:
            dates.remove(time)
        for date in dates:
            counts.append((date, 0))
        counts = sorted(counts, key=itemgetter(0))
        reports.append((str(osr), counts))

    cached = render_template("summary/index_plot_data.html",
                             reports=reports,
                             resolution=filter_form.resolution.data[0])

    flask_cache.set(key, cached, timeout=60*60)
    return cached


@summary.route("/")
def index():
    filter_form = SummaryForm(request.args)
    reports = []
    if filter_form.validate():

        index_plot_data = index_plot_data_cache(filter_form)
        return render_template("summary/index.html",
                               filter_form=filter_form,
                               index_plot_data=index_plot_data)

    return render_template("summary/index.html",
                           filter_form=filter_form,
                           reports=reports,
                           resolution=filter_form.resolution.data[0])
