from tortoise import fields
from tortoise.models import Model


class UserToken(Model):
    id = fields.IntField(pk=True)
    user_id = fields.CharField(max_length=128)  # ID пользователя из Яндекс OAuth
    provider = fields.CharField(max_length=32)  # 'yandex'
    access_token = fields.CharField(max_length=2048)
    refresh_token = fields.CharField(max_length=2048, null=True)
    expires_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_tokens"


