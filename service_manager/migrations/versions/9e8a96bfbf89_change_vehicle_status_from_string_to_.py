"""Change vehicle status from String to Boolean

Revision ID: 9e8a96bfbf89
Revises: 1abc2c43690e
Create Date: 2025-08-25 23:46:57.467771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e8a96bfbf89'
down_revision: Union[str, Sequence[str], None] = '1abc2c43690e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with data conversion."""

    # 1. Convert text values into proper boolean values
    op.execute("UPDATE vehicles SET status = 'True' WHERE status = 'ACTIVE'")
    op.execute("UPDATE vehicles SET status = 'False' WHERE status IN ('INACTIVE', 'MAINTENANCE')")

    # 2. Now alter the column using explicit USING clause
    op.execute("""
        ALTER TABLE vehicles
        ALTER COLUMN status TYPE BOOLEAN
        USING status::BOOLEAN
    """)

    # 3. Optionally set default to True at DB level
    op.execute("ALTER TABLE vehicles ALTER COLUMN status SET DEFAULT True")

    # 4. Update comment
    op.execute("COMMENT ON COLUMN vehicles.status IS 'Vehicle status - True: Active, False: Inactive'")


def downgrade() -> None:
    """Downgrade schema with reverse conversion."""

    # 1. Convert back to text for safety
    op.execute("ALTER TABLE vehicles ALTER COLUMN status DROP DEFAULT")

    op.execute("""
        ALTER TABLE vehicles
        ALTER COLUMN status TYPE VARCHAR
        USING status::VARCHAR
    """)

    # 2. Restore original text values
    op.execute("UPDATE vehicles SET status = 'ACTIVE' WHERE status = True")
    op.execute("UPDATE vehicles SET status = 'INACTIVE' WHERE status = False")

    # 3. Restore comment
    op.execute("COMMENT ON COLUMN vehicles.status IS 'Vehicle status like ACTIVE, INACTIVE, MAINTENANCE'")
