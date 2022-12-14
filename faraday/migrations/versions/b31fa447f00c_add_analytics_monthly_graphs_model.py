"""add analytics monthly graphs model

Revision ID: b31fa447f00c
Revises: be1f942eba28
Create Date: 2022-03-17 17:42:11.963768+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b31fa447f00c'
down_revision = 'be1f942eba28'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vulnerability_hit_count',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('workspace_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('low_open_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('low_open_confirmed', sa.Integer(), nullable=False),
    sa.Column('low_risk_accepted_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('low_risk_accepted_confirmed', sa.Integer(), nullable=False),
    sa.Column('low_re_opened_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('low_re_opened_confirmed', sa.Integer(), nullable=False),
    sa.Column('low_closed_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('low_closed_confirmed', sa.Integer(), nullable=False),
    sa.Column('medium_open_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('medium_open_confirmed', sa.Integer(), nullable=False),
    sa.Column('medium_risk_accepted_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('medium_risk_accepted_confirmed', sa.Integer(), nullable=False),
    sa.Column('medium_re_opened_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('medium_re_opened_confirmed', sa.Integer(), nullable=False),
    sa.Column('medium_closed_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('medium_closed_confirmed', sa.Integer(), nullable=False),
    sa.Column('high_open_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('high_open_confirmed', sa.Integer(), nullable=False),
    sa.Column('high_risk_accepted_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('high_risk_accepted_confirmed', sa.Integer(), nullable=False),
    sa.Column('high_re_opened_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('high_re_opened_confirmed', sa.Integer(), nullable=False),
    sa.Column('high_closed_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('high_closed_confirmed', sa.Integer(), nullable=False),
    sa.Column('critical_open_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('critical_open_confirmed', sa.Integer(), nullable=False),
    sa.Column('critical_risk_accepted_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('critical_risk_accepted_confirmed', sa.Integer(), nullable=False),
    sa.Column('critical_re_opened_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('critical_re_opened_confirmed', sa.Integer(), nullable=False),
    sa.Column('critical_closed_unconfirmed', sa.Integer(), nullable=False),
    sa.Column('critical_closed_confirmed', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspace.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vulnerability_hit_count_workspace_id'), 'vulnerability_hit_count', ['workspace_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_vulnerability_hit_count_workspace_id'), table_name='vulnerability_hit_count')
    op.drop_table('vulnerability_hit_count')
    # ### end Alembic commands ###
