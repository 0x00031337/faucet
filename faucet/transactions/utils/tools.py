import os
import binascii
import hashlib
from decimal import Decimal
import datetime
import logging

from django.conf import settings
from django.db.models import Count
from ..models import Transaction

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# For converting from float to XMR notation
PICO_XMR = Decimal("0.000000000001")


def xmr_to_float(value):
    """Converts an integer value in the XMR format to a float.

    The float format has a maxium of 12 decimal digits.

    :param value: value to convert from XMR notation to float
    :returns: converted value in float
    """

    return (Decimal(value) * PICO_XMR).quantize(PICO_XMR)


def float_to_xmr(value):
    """Converts a float value to an integer in the XMR notation.

    The float format has a maxium of 12 decimal digits.

    :param value: value to convert from float to XMR notation
    :returns: converted value in XMR notation
    """

    return int(Decimal(value) / PICO_XMR)


def generate_xmr_payment_id_long():
    """Payment ID old format
    """
    paymentId = binascii.hexlify(os.urandom(32))
    return bytes.decode(paymentId)


def generate_xmr_payment_id_short():
    """Payment ID integrated address
    """
    paymentId = binascii.hexlify(os.urandom(8))
    return bytes.decode(paymentId)


def hash_value(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def addr_withdrew_too_often(destination_address, rate_allowed, days):
    """Block destination addresses which withdraw too often.

    Look back a number of days and check the allowed number of withdrawals for
    a destination address.

    :param rate_allowed: number of allowed withdrawals within the given days
    :param days: range of days to consider
    :returns: True if payout is blocked (number of payouts for address is above limits), false otherwise
    """

    suspicious_withdrawals = (
        Transaction.objects.filter(
            timestamp__lte=datetime.datetime.today(),
            timestamp__gt=datetime.datetime.today()
            - datetime.timedelta(days=days),
        )
        .values("destination_address")
        .annotate(count=Count("destination_address"))
    )
    suspicious_addresses = [
        addr["destination_address"]
        for addr in suspicious_withdrawals
        if addr["count"] >= rate_allowed
    ]

    return destination_address in suspicious_addresses
