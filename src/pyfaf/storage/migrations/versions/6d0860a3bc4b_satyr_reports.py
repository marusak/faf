# Copyright (C) 2017  ABRT Team
# Copyright (C) 2017  Red Hat, Inc.
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


"""Satyr reports

Revision ID: 6d0860a3bc4b
Revises: 168c63b81f85
Create Date: 2017-06-22 09:33:39.504703

"""

# revision identifiers, used by Alembic.
revision = '6d0860a3bc4b'
down_revision = '168c63b81f85'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('satyrreports',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('report_id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
                   )

def downgrade():
    op.drop_table('urlrepo')
