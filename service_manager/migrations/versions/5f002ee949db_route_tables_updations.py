"""route tables updations

Revision ID: 5f002ee949db
Revises: f8cf8aba508a
Create Date: 2025-08-26 17:02:18.980806
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5f002ee949db'
down_revision: Union[str, Sequence[str], None] = 'f8cf8aba508a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # -----------------------------
    # 1️⃣ Create bookingstatus enum
    # -----------------------------
    op.execute("""
        CREATE TYPE bookingstatus AS ENUM (
            'PENDING', 'CONFIRMED', 'ONGOING', 'PICKED_UP', 
            'COMPLETED', 'CANCELLED', 'NO_SHOW'
        )
    """)

    # -----------------------------
    # 2️⃣ Fix existing data (case-sensitive)
    # -----------------------------
    op.execute("UPDATE bookings SET status = 'PENDING' WHERE status ILIKE 'pending'")
    op.execute("UPDATE bookings SET status = 'CONFIRMED' WHERE status ILIKE 'confirmed'")
    op.execute("UPDATE bookings SET status = 'ONGOING' WHERE status ILIKE 'ongoing'")
    op.execute("UPDATE bookings SET status = 'PICKED_UP' WHERE status ILIKE 'picked_up'")
    op.execute("UPDATE bookings SET status = 'COMPLETED' WHERE status ILIKE 'completed'")
    op.execute("UPDATE bookings SET status = 'CANCELLED' WHERE status ILIKE 'cancelled'")
    op.execute("UPDATE bookings SET status = 'NO_SHOW' WHERE status ILIKE 'no_show'")

    # -----------------------------
    # 3️⃣ Alter bookings.status column
    # -----------------------------
    op.alter_column(
        'bookings',
        'status',
        existing_type=sa.VARCHAR(length=50),
        type_=sa.Enum(
            'PENDING', 'CONFIRMED', 'ONGOING', 'PICKED_UP', 
            'COMPLETED', 'CANCELLED', 'NO_SHOW',
            name='bookingstatus'
        ),
        postgresql_using='status::text::bookingstatus',
        nullable=False
    )

    # -----------------------------
    # 4️⃣ Convert shift_route_stops.booking_id to Integer
    # -----------------------------
    op.alter_column(
        'shift_route_stops',
        'booking_id',
        existing_type=sa.VARCHAR(),
        type_=sa.Integer(),
        postgresql_using='booking_id::integer',
        existing_nullable=False
    )

    # -----------------------------
    # 5️⃣ Add foreign key from shift_route_stops.booking_id -> bookings.booking_id
    # -----------------------------
    op.create_foreign_key(
        constraint_name='fk_shift_route_stops_booking_id',
        source_table='shift_route_stops',
        referent_table='bookings',
        local_cols=['booking_id'],
        remote_cols=['booking_id']
    )

    # -----------------------------
    # 6️⃣ Create routestatus enum before adding column
    # -----------------------------
    op.execute("""
        CREATE TYPE routestatus AS ENUM (
            'CONFIRMED',
            'ASSIGNED_TO_VENDOR',
            'DRIVER_ASSIGNED',
            'IN_PROGRESS',
            'COMPLETED',
            'CANCELLED'
        )
    """)

    # -----------------------------
    # 7️⃣ Add shift_routes.status enum column
    # -----------------------------
    op.add_column(
        'shift_routes',
        sa.Column(
            'status',
            sa.Enum(
                'CONFIRMED', 'ASSIGNED_TO_VENDOR', 'DRIVER_ASSIGNED',
                'IN_PROGRESS', 'COMPLETED', 'CANCELLED',
                name='routestatus'
            ),
            nullable=False
        )
    )

    # -----------------------------
    # 8️⃣ Drop shift_routes.confirmed column
    # -----------------------------
    op.drop_column('shift_routes', 'confirmed')


def downgrade() -> None:
    """Downgrade schema."""
    # -----------------------------
    # 1️⃣ Restore shift_routes.confirmed column
    # -----------------------------
    op.add_column(
        'shift_routes',
        sa.Column('confirmed', sa.BOOLEAN(), nullable=False, server_default=sa.text('false'))
    )

    # -----------------------------
    # 2️⃣ Drop shift_routes.status column and routestatus enum
    # -----------------------------
    op.drop_column('shift_routes', 'status')
    op.execute('DROP TYPE IF EXISTS routestatus')

    # -----------------------------
    # 3️⃣ Drop foreign key from shift_route_stops.booking_id
    # -----------------------------
    op.drop_constraint('fk_shift_route_stops_booking_id', 'shift_route_stops', type_='foreignkey')

    # -----------------------------
    # 4️⃣ Convert shift_route_stops.booking_id back to VARCHAR
    # -----------------------------
    op.alter_column(
        'shift_route_stops',
        'booking_id',
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(),
        existing_nullable=False
    )

    # -----------------------------
    # 5️⃣ Convert bookings.status back to VARCHAR and drop bookingstatus enum
    # -----------------------------
    op.alter_column(
        'bookings',
        'status',
        existing_type=sa.Enum(
            'PENDING', 'CONFIRMED', 'ONGOING', 'PICKED_UP',
            'COMPLETED', 'CANCELLED', 'NO_SHOW',
            name='bookingstatus'
        ),
        type_=sa.VARCHAR(length=50),
        postgresql_using='status::text',
        nullable=True
    )
    op.execute('DROP TYPE IF EXISTS bookingstatus')
