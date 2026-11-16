"""${message}"""

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    # 自动生成后必须检查约束、数据兼容与回填策略。
    ${upgrades if upgrades else "pass"}


def downgrade():
    # 降级可能删除数据，执行前必须确认实际影响。
    ${downgrades if downgrades else "pass"}
