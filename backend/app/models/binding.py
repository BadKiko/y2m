from tortoise import fields
from tortoise.models import Model


class Binding(Model):
    id = fields.IntField(pk=True)
    device = fields.ForeignKeyField("models.Device", related_name="bindings")
    capability = fields.CharField(max_length=128)  # e.g. on, off, toggle, set_volume, etc.
    action_type = fields.CharField(max_length=64)  # e.g. adb, station
    action_config = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "bindings"


