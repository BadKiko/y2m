from tortoise import fields
from tortoise.models import Model


class Device(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    yandex_type = fields.CharField(max_length=64)
    # optional network params for ADB
    adb_host = fields.CharField(max_length=255, null=True)
    adb_port = fields.IntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "devices"


