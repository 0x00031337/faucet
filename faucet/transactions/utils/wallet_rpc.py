from django.conf import settings

import requests
import logging

from . import tools
from ..exceptions import RpcConnectionError, GetBalanceError, GetAmountError
from monerorpc.authproxy import AuthServiceProxy, JSONRPCException

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WalletRPC:
    """Interface to monero-wallet-rpc.

    Uses on python-monerorpc as backend.
    """

    network_type = None

    @staticmethod
    def get_balance():
        """Returns the current balance of the wallet.

        :returns: unlocked_balance if successful in XMR format
        :raises RpcConnectionError: no connection could be established
        :raises ValueError: retrieved data could not be processed
        """

        # get the current balance
        rpc_connection = AuthServiceProxy(
            "http://{0}:{1}/json_rpc".format(
                settings.WALLET_HOST, settings.WALLET_PORT
            )
        )

        result = None
        try:
            result = rpc_connection.getbalance()
        except (
            requests.HTTPError,
            requests.ConnectionError,
            JSONRPCException,
        ) as e:
            logger.error("RPC Error on getting balance" + str(e))
            raise RpcConnectionError(str(e))
        balance = result.get("unlocked_balance", None)
        # check unlocked_balance key
        # balance can be 0, therefore check for None
        if balance is None:
            raise ValueError("Error with: {0}".format(result))

        return balance

    @staticmethod
    def get_address():
        """Returns the current wallet's address.

        :returns: wallet's address if successful
        :raises RpcConnectionError: no connection could be established
        :raises ValueError: retrieved data could not be processed
        """

        # get the wallet's address
        rpc_connection = AuthServiceProxy(
            "http://{0}:{1}/json_rpc".format(
                settings.WALLET_HOST, settings.WALLET_PORT
            )
        )

        result = None
        try:
            result = rpc_connection.get_address()
        except (
            requests.HTTPError,
            requests.ConnectionError,
            JSONRPCException,
        ) as e:
            logger.error("RPC Error on getting address" + str(e))
            logger.exception(e)
            raise RpcConnectionError(str(e))
        address = result.get("address", None)
        # check address
        if not address:
            raise ValueError("Eror with: {0}".format(result))

        return address

    @staticmethod
    def make_transaction(destination_address, amount):
        """Makes a transaction to the given address.

        :param destination_address: the wallet address to send XMR to
        :param amount: the amount of XMR to send
        :returns: the complete transaction object including user's IP address
        :raises RpcConnectionError: in case of a connection error to the rpc
        :raises ValueError: in case  the JSON returned is bad
        """

        # send xmr to given destination_address
        recipients = [{"address": destination_address, "amount": amount}]

        # transfer parameters
        params = {"destinations": recipients, "mixin": settings.DEFAULT_MIXIN}

        if len(destination_address) == 95:
            # payment id
            payment_id = tools.generate_xmr_payment_id_long()
            params.update({"payment_id": payment_id})

        # get the wallet's address
        rpc_connection = AuthServiceProxy(
            "http://{0}:{1}/json_rpc".format(
                settings.WALLET_HOST, settings.WALLET_PORT
            )
        )

        result = None
        try:
            result = rpc_connection.transfer_split(params)
        except (
            requests.HTTPError,
            requests.ConnectionError,
            JSONRPCException,
        ) as e:
            logger.error("RPC Error on making transaction" + str(e))
            raise RpcConnectionError(str(e))
        # transfer returns a single tx_hash
        # tarnsfer_split returns a list of tx_hash -> tx_hash_list
        transaction_id = result.get("tx_hash_list", list())
        # check tx_hash_list key
        if not transaction_id:
            raise ValueError("Error with: {0}".format(result))

        transaction = dict()
        transaction.update(
            {
                "transaction_id": ",".join(transaction_id),
                "destination_address": destination_address,
                "amount": amount,
            }
        )

        return transaction

    @classmethod
    def get_network_type(cls):
        """Returns the monero network type the faucet is running on.

        :returns: network type (stagenet, testnet)
        :raises RpcConnectionError: no connection could be established
        :raises ValueError: retrieved data could not be processed
        """
        if not cls.network_type:
            rpc_connection = AuthServiceProxy(
                "http://{0}:{1}/json_rpc".format(
                    settings.DAEMON_HOST, settings.DAEMON_PORT
                )
            )

            result = None
            try:
                result = rpc_connection.get_info()
            except (
                requests.HTTPError,
                requests.ConnectionError,
                JSONRPCException,
            ) as e:
                logger.error("RPC Error on getting address" + str(e))
                logger.exception(e)
                raise RpcConnectionError(str(e))
            # Check network type
            network_type = result.get("nettype", None)
            if not network_type:
                raise ValueError("Error with: {0}".format(result))
            cls.network_type = network_type
        return cls.network_type


def get_balance():
    try:
        return WalletRPC.get_balance()
    except (ValueError, RpcConnectionError) as e:
        raise GetBalanceError("Could not get balance.")


def get_amount(factor):
    """Returns the calculated amount to transfer.

    :param factor: the factor to consider when paying out XMR
    :returns: the XMR to pay out (factored unlocked_balance)
    """
    balance = get_balance()
    if factor <= 0:
        logger.error("Wrong factor provided: " + str(factor))
        raise GetAmountError("FACTOR=" + str(factor))

    return balance // factor
