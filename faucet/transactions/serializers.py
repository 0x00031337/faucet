import logging

from rest_framework import serializers
from django.conf import settings
from django.core.validators import MinLengthValidator

from .models import Transaction
from .exceptions import RpcConnectionError, MakeTransactionError

from .utils.wallet_rpc import WalletRPC, get_amount
from .utils import tools

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def wallet_address_validator(address):
    """Validate the destination address.

    :param address: the address to be validated
    :returns: the address if valid
    :raises serializers.ValidationError: if the address should not be valid
    """

    address_length = len(address)
    if 95 != address_length and 106 != address_length:
        raise serializers.ValidationError("Address too short/long.")
    return address


class TransactionSerializer(serializers.ModelSerializer):
    """Serializes fields of the actual transaction object.
    """

    destination_address = serializers.CharField(
        validators=[wallet_address_validator]
    )
    transaction_id = serializers.CharField(
        validators=[MinLengthValidator(64)], required=False
    )
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ("amount", "transaction_id", "destination_address")
        read_only_fields = ("amount", "transaction_id")

    def save(self, **kwargs):
        try:
            transaction = WalletRPC.make_transaction(
                destination_address=self.validated_data.get(
                    "destination_address"
                ),
                amount=get_amount(settings.FACTOR_BALANCE),
            )
            self.validated_data.update(transaction)
            logger.info("store tx {}".format(transaction))
            return super().save(**kwargs)
        except (ValueError, RpcConnectionError) as e:
            logger.error(str(e))
            raise MakeTransactionError(str(e))

    def get_amount(self, obj):
        return tools.xmr_to_float(obj.amount)
