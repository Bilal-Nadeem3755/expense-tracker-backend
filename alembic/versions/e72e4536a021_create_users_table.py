"""create users table

Revision ID: e72e4536a021
Revises:
Create Date: 2026-09-02 23:36:32.107217

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e72e4536a021'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_index(
        op.f('ix_users_email'),
        'users',
        ['email'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_users_email'),
        table_name='users'
    )

    op.drop_table('users')