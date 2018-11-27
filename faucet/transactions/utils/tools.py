import os
import binascii
import hashlib
from decimal import Decimal

# For converting from float to XMR notation
PICO_XMR = Decimal("0.000000000001")


def xmr_to_float(value):
    """Converts an integer value in the XMR format to a notation.

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
