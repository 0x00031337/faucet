from django.db import models


class Transaction(models.Model):
    """Represents a monero withdrawal from the wallet.
    """

    amount = models.BigIntegerField()
    destination_address = models.TextField(max_length=95)
    transaction_id = models.TextField()
    ip_address_hash = models.TextField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Converts the object to string and only returns most relevant information.
        """

        return self.transaction_id
