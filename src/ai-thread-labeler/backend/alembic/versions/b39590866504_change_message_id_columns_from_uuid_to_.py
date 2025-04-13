from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'change_message_id_to_string'
down_revision = '83dca7551ed4'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing FKs
    op.drop_constraint('classifications_message_id_fkey', 'classifications', type_='foreignkey')
    op.drop_constraint('embeddings_message_id_fkey', 'embeddings', type_='foreignkey')
    op.drop_constraint('processed_messages_message_id_fkey', 'processed_messages', type_='foreignkey')
    op.drop_constraint('thread_labels_message_id_fkey', 'thread_labels', type_='foreignkey')
    op.drop_constraint('thread_labels_solution_message_id_fkey', 'thread_labels', type_='foreignkey')

    # Alter column types
    op.alter_column('classifications', 'message_id', type_=sa.String(), existing_type=sa.dialects.postgresql.UUID)
    op.alter_column('embeddings', 'message_id', type_=sa.String(), existing_type=sa.String())  # already String, safe
    op.alter_column('processed_messages', 'message_id', type_=sa.String(), existing_type=sa.dialects.postgresql.UUID)
    op.alter_column('thread_labels', 'message_id', type_=sa.String(), existing_type=sa.dialects.postgresql.UUID)
    op.alter_column('thread_labels', 'solution_message_id', type_=sa.String(), existing_type=sa.dialects.postgresql.UUID)

    # Add new FKs to messages.message_id (string)
    op.create_foreign_key(
        'classifications_message_id_fkey',
        'classifications', 'messages',
        ['message_id'], ['message_id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'embeddings_message_id_fkey',
        'embeddings', 'messages',
        ['message_id'], ['message_id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'processed_messages_message_id_fkey',
        'processed_messages', 'messages',
        ['message_id'], ['message_id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'thread_labels_message_id_fkey',
        'thread_labels', 'messages',
        ['message_id'], ['message_id']
    )
    op.create_foreign_key(
        'thread_labels_solution_message_id_fkey',
        'thread_labels', 'messages',
        ['solution_message_id'], ['message_id']
    )


def downgrade():
    # Reverse everything — adjust if needed
    op.drop_constraint('classifications_message_id_fkey', 'classifications', type_='foreignkey')
    op.drop_constraint('embeddings_message_id_fkey', 'embeddings', type_='foreignkey')
    op.drop_constraint('processed_messages_message_id_fkey', 'processed_messages', type_='foreignkey')
    op.drop_constraint('thread_labels_message_id_fkey', 'thread_labels', type_='foreignkey')
    op.drop_constraint('thread_labels_solution_message_id_fkey', 'thread_labels', type_='foreignkey')

    op.alter_column('classifications', 'message_id', type_=sa.dialects.postgresql.UUID)
    op.alter_column('processed_messages', 'message_id', type_=sa.dialects.postgresql.UUID)
    op.alter_column('thread_labels', 'message_id', type_=sa.dialects.postgresql.UUID)
    op.alter_column('thread_labels', 'solution_message_id', type_=sa.dialects.postgresql.UUID)

    op.create_foreign_key(
        'classifications_message_id_fkey',
        'classifications', 'messages',
        ['message_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'embeddings_message_id_fkey',
        'embeddings', 'messages',
        ['message_id'], ['message_id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'processed_messages_message_id_fkey',
        'processed_messages', 'messages',
        ['message_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'thread_labels_message_id_fkey',
        'thread_labels', 'messages',
        ['message_id'], ['id']
    )
    op.create_foreign_key(
        'thread_labels_solution_message_id_fkey',
        'thread_labels', 'messages',
        ['solution_message_id'], ['id']
    )
