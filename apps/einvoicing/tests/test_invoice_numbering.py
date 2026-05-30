"""Tests de la numérotation séparée pour avoirs.

L'art. 289 CGI impose une séquence chronologique continue. La séquence
classique `FAC-AAAA-XXX` reste sacrée. Les avoirs ont une séquence dédiée
`AVO-AAAA-XXXXX` pour ne pas perturber la séquence des factures émises.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.codelists import InvoiceTypeCode
from apps.factures.models import Invoice


pytestmark = pytest.mark.django_db


def _make_client() -> ClientProfile:
    return ClientProfile.objects.create(
        full_name="Acme SARL",
        email="acme@example.com",
    )


class TestInvoiceNumbering:
    def test_invoice_keeps_legacy_format(self) -> None:
        inv = Invoice.objects.create(client=_make_client())
        assert inv.number.startswith("FAC-")
        assert inv.number.endswith("-001")

    def test_credit_note_has_dedicated_sequence(self) -> None:
        client = _make_client()
        inv = Invoice.objects.create(client=client)
        avoir = Invoice.objects.create(
            client=client,
            credit_note_for=inv,
            is_credit_note=True,
        )
        assert avoir.number.startswith("AVO-")
        assert avoir.number.endswith("-00001")
        # Le code type est forcé à credit_note même si l'appelant ne le précise pas
        assert avoir.invoice_type_code == InvoiceTypeCode.CREDIT_NOTE

    def test_credit_note_sequence_is_independent(self) -> None:
        """Créer un avoir ne consomme pas un numéro de la séquence facture."""
        client = _make_client()
        inv1 = Invoice.objects.create(client=client)
        Invoice.objects.create(client=client, is_credit_note=True)  # AVO-...-00001
        inv2 = Invoice.objects.create(client=client)  # doit être FAC-...-002
        # Les deux factures se suivent, indépendamment de l'avoir
        n1 = int(inv1.number.rsplit("-", 1)[-1])
        n2 = int(inv2.number.rsplit("-", 1)[-1])
        assert n2 == n1 + 1
