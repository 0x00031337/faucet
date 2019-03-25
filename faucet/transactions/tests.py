from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from rest_framework.test import APITestCase

from .exceptions import MakeTransactionError
from .models import Transaction

from unittest import mock
import logging
from decimal import Decimal

from .utils import tools
from .utils.wallet_rpc import WalletRPC
from .utils.wallet_rpc import AuthServiceProxy

# logging.basicConfig()
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def mocked_get_balance():
    return 19769691509258199


def mocked_make_rpc_success(url, rpc_input, headers):
    class RpcResponse:
        def json(self):
            return {
                "id": "0",
                "jsonrpc": "2.0",
                "result": {
                    "amount_list": [3000000000000],
                    "fee_list": [85106400000],
                    "multisig_txset": "",
                    "tx_hash_list": [
                        "c8d815f48f27d53fdaf198a74b292a91bfaf87529a9a9a9ee66079a890b3b58b"
                    ],
                    "unsigned_txset": "",
                },
            }

    return RpcResponse()


def mocked_make_transaction(destination_address, amount):
    transaction = dict()
    transaction.update(
        {
            "transaction_id": "c8d815f48f27d53fdaf198a74b292a91bfaf87529a9a9a9ee66079a890b3b58b",
            "destination_address": destination_address,
            "amount": amount,
        }
    )

    return transaction


def mocked_get_client_ip_error(_):
    raise MakeTransactionError()


# TransactionsView test case
class TransactionsApiViewTests(TestCase):
    def test_no_data_sent(self):
        """If no data was sent.
        """

        response = self.client.post("/transactions/", data={})
        self.assertEqual(response.status_code, 400)
        response.json().get("destination_address")
        self.assertIn("destination_address", response.json())
        self.assertIn(
            "This field is required.",
            response.json().get("destination_address"),
        )

    def test_destination_address_empty(self):
        """If the address is empty.

        Post an empty address.19769691509258199
        """

        too_short = ""
        response = self.client.post(
            "/transactions/", data={"destination_address": too_short}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("destination_address", response.json())
        self.assertIn(
            "This field may not be blank.",
            response.json().get("destination_address"),
        )

    def test_destination_address_too_short(self):
        """If the address is too short.

        Post an address that is shorter than expected.
        """

        too_short = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZ"
        response = self.client.post(
            "/transactions/", data={"destination_address": too_short}
        )
        self.assertEqual(response.status_code, 400)

    def test_destination_address_too_long(self):
        """If the address is too long.

        Post an address that is one character longer than expceted.
        """

        too_long = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZT1"
        response = self.client.post(
            "/transactions/", data={"destination_address": too_long}
        )
        self.assertEqual(response.status_code, 400)

    def test_destination_integrated_address_too_short(self):
        """If the integrated address is too short.

        Post an integrated address that is shorter than expected.
        """

        too_short = "5KR5fayZWUWixRyVnDRrhKGiA7UBHujuqakhxem7tmUS6MLpeeFWCgpcoQaxSpfzTeKUHTfd8nn4sDG8uTKqdunZhW8B3xaDLUfGgjMob"
        response = self.client.post(
            "/transactions/", data={"destination_address": too_short}
        )
        self.assertEqual(response.status_code, 400)

    def test_destination_integrated_address_too_long(self):
        """If the integrated address is too long.

        Post an integrated address that is one character longer than expected.
        """

        too_long = "5KR5fayZWUWixRyVnDRrhKGiA7UBHujuqakhxem7tmUS6MLpeeFWCgpcoQaxSpfzTeKUHTfd8nn4sDG8uTKqdunZhW8B3xaDLUfGgjMobn1"
        response = self.client.post(
            "/transactions/", data={"destination_address": too_long}
        )
        self.assertEqual(response.status_code, 400)

    def test_float_to_xmr(self):
        """A float should be converted to the correct xmr notation.
        """

        float_value = 12
        xmr_notation = tools.float_to_xmr(float_value)
        self.assertEqual(xmr_notation, 12000000000000)

        float_value = "4.76"
        xmr_notation = tools.float_to_xmr(float_value)
        self.assertEqual(xmr_notation, 4760000000000)

        float_value = "0.08"
        xmr_notation = tools.float_to_xmr(float_value)
        self.assertEqual(xmr_notation, 80000000000)

    def test_xmr_to_float(self):
        """A value in xmr notation should be converted into the float value.
        """

        float_value = Decimal(12000000000000)
        xmr_notation = tools.xmr_to_float(float_value)
        self.assertEqual(xmr_notation, 12)

        xmr_notation = 4760000000000
        float_value = tools.xmr_to_float(xmr_notation)
        self.assertEqual(float_value, Decimal("4.76").quantize(tools.PICO_XMR))

        xmr_notation = 80000000000
        float_value = tools.xmr_to_float(xmr_notation)
        self.assertEqual(float_value, Decimal("0.08").quantize(tools.PICO_XMR))

    def test_xmr_to_float_interchangeable(self):
        """Xmr notation and float should be interchangeable.
        """

        xmr_notation = 80000000000
        float_value = tools.xmr_to_float(xmr_notation)
        self.assertEqual(tools.float_to_xmr(float_value), xmr_notation)

        float_value = Decimal("4.76").quantize(tools.PICO_XMR)
        xmr_notation = tools.float_to_xmr(float_value)
        self.assertEqual(tools.xmr_to_float(xmr_notation), float_value)


class TransactionsApiViewTests_Api(APITestCase):
    @mock.patch.object(WalletRPC, "get_balance", mocked_get_balance)
    @mock.patch.object(
        AuthServiceProxy, "_get_response", mocked_make_rpc_success
    )
    @mock.patch.object(WalletRPC, "make_transaction", mocked_make_transaction)
    def test_successful_transaction(self):
        """A successful transaction using a Monero address.

        POST /transactions/
        Requests to the wallet are mocked.
        """

        destination_address = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZT"

        response = self.client.post(
            "/transactions/", data={"destination_address": destination_address}
        )
        self.assertEqual(response.status_code, 201)

        transaction = response.json()

        # create a mocked transaction
        mocked_transaction = mocked_make_transaction(
            destination_address=destination_address, amount=0
        )
        mocked_transaction["amount"] = min(
            settings.MAXIMUM_PAYOUT,
            tools.xmr_to_float(
                mocked_get_balance() // settings.FACTOR_BALANCE
            ),
        )

        # self.assertAlmostEqual(transaction.get("amount"), mocked_transaction.get("amount"))
        self.assertEqual(
            transaction.get("amount"), float(mocked_transaction.get("amount"))
        )

        # in order to compare very long strings like destination_address
        self.maxDiff = None
        self.assertEqual(
            transaction.get("destination_address"),
            mocked_transaction.get("destination_address"),
        )
        self.assertEqual(
            transaction.get("transaction_id"),
            mocked_transaction.get("transaction_id"),
        )
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(
            Transaction.objects.get().destination_address, destination_address
        )
        self.assertNotIn(
            "ip_address_hash", Transaction.objects.get().ip_address_hash
        )

    @mock.patch.object(WalletRPC, "get_balance", mocked_get_balance)
    @mock.patch.object(
        AuthServiceProxy, "_get_response", mocked_make_rpc_success
    )
    @mock.patch.object(WalletRPC, "make_transaction", mocked_make_transaction)
    def test_rate_limitation_by_withdrawals(self):
        """Destination addresses are allowed a specific number of withdrawals per day.

        POST /transactions/
        Requests to the wallet are mocked.
        """

        destination_address = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZT"

        # Same destination_address is allowed to withdraw only ADDRESS_RATE_PER_DAY times per day.
        for i in range(settings.ADDRESS_RATE_PER_DAY):
            response = self.client.post(
                "/transactions/",
                data={"destination_address": destination_address},
            )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(Transaction.objects.count(), i + 1)

        # Next withdrawal is blocked.
        response = self.client.post(
            "/transactions/", data={"destination_address": destination_address}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Transaction.objects.count(), i + 1)

    @mock.patch.object(WalletRPC, "get_balance", mocked_get_balance)
    @mock.patch.object(
        AuthServiceProxy, "_get_response", mocked_make_rpc_success
    )
    @mock.patch.object(WalletRPC, "make_transaction", mocked_make_transaction)
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limitation_by_IP(self):
        """IPs are allowed once every settings.ONCE_EVERY_N_MINUTE minute.

        POST /transactions/
        Requests to the wallet are mocked.
        """

        destination_address = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZT"

        # IP is allowed to once.
        response = self.client.post(
            "/transactions/", data={"destination_address": destination_address}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Transaction.objects.count(), 1)

        # Next withdrawal is blocked.
        response = self.client.post(
            "/transactions/", data={"destination_address": destination_address}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Transaction.objects.count(), 1)

    @mock.patch.object(WalletRPC, "get_balance", mocked_get_balance)
    def test_get_current_balance(self):
        """The current balance is returned.

        GET /transactions/
        Requests to the wallet are mocked.
        """

        response = self.client.get("/transactions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json().get("balance"),
            int(tools.xmr_to_float(mocked_get_balance())),
        )

    @mock.patch.object(WalletRPC, "get_balance", mocked_get_balance)
    @mock.patch("transactions.views.get_client_ip", mocked_get_client_ip_error)
    @mock.patch.object(WalletRPC, "make_transaction", mocked_make_transaction)
    def test_missing_ip_in_transaction(self):
        """A transacton needs an IP when stored into the database.

        POST /transactions/
        Requests to the wallet are mocked.
        """

        destination_address = "55YjCnmQ6NgM52yccJk23cR55h6wmuzw1fEHfeNVbdtPJ2v8GoByB9XDDi89dqhC4pTYRdssorqGWiXWeVywKVjtA8m5MZT"

        response = self.client.post(
            "/transactions/", data={"destination_address": destination_address}
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(Transaction.objects.count(), 0)
