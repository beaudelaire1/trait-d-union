"""
CRM Integration Service — Intégration avec CRM externes

Ce module gère la synchronisation des leads avec :
- Airtable (via API REST)
- HubSpot (via API REST)

Configuration (.env):
    # Airtable
    AIRTABLE_API_KEY=patXXX
    AIRTABLE_BASE_ID=appXXX
    AIRTABLE_TABLE_NAME=Leads

    # HubSpot
    HUBSPOT_API_KEY=pat-xxx
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class AirtableService:
    """Service d'intégration Airtable."""

    BASE_URL = "https://api.airtable.com/v0"

    def __init__(self):
        self.api_key = os.environ.get('AIRTABLE_API_KEY', '')
        self.base_id = os.environ.get('AIRTABLE_BASE_ID', '')
        self.table_name = os.environ.get('AIRTABLE_TABLE_NAME', 'Leads')

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_id)

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def _endpoint(self) -> str:
        return f"{self.BASE_URL}/{self.base_id}/{self.table_name}"

    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Crée un lead dans Airtable.

        Args:
            lead_data: Dictionnaire avec les champs du lead

        Returns:
            ID de l'enregistrement Airtable ou None si erreur
        """
        if not self.is_configured:
            logger.warning("Airtable non configuré, lead non synchronisé")
            return None

        # Mapper les champs Django vers Airtable
        fields = {
            'Nom': lead_data.get('name', ''),
            'Email': lead_data.get('email', ''),
            'Téléphone': lead_data.get('phone', ''),
            'Message': lead_data.get('message', ''),
            'Source': lead_data.get('source', 'Website'),
            'Statut': 'Nouveau',
            'Date': datetime.now().strftime('%Y-%m-%d'),
        }

        # Ajouter les champs optionnels
        if lead_data.get('company'):
            fields['Entreprise'] = lead_data['company']
        if lead_data.get('budget'):
            fields['Budget'] = lead_data['budget']
        if lead_data.get('service'):
            fields['Service'] = lead_data['service']

        payload = {'fields': fields}

        try:
            response = requests.post(
                self._endpoint(),
                headers=self._headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            record = response.json()
            record_id = record.get('id')
            logger.info(f"Lead créé dans Airtable: {record_id}")
            return record_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur Airtable: {e}")
            return None

    def update_lead(self, record_id: str, fields: Dict[str, Any]) -> bool:
        """Met à jour un lead existant dans Airtable."""
        if not self.is_configured or not record_id:
            return False

        try:
            response = requests.patch(
                f"{self._endpoint()}/{record_id}",
                headers=self._headers(),
                json={'fields': fields},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Lead Airtable mis à jour: {record_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur mise à jour Airtable: {e}")
            return False


class HubSpotService:
    """Service d'intégration HubSpot."""

    BASE_URL = "https://api.hubapi.com"

    def __init__(self):
        self.api_key = os.environ.get('HUBSPOT_API_KEY', '')

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def create_contact(self, contact_data: Dict[str, Any]) -> Optional[str]:
        """
        Crée un contact dans HubSpot.

        Args:
            contact_data: Dictionnaire avec les infos du contact

        Returns:
            ID du contact HubSpot ou None si erreur
        """
        if not self.is_configured:
            logger.warning("HubSpot non configuré, contact non synchronisé")
            return None

        properties = {
            'email': contact_data.get('email', ''),
            'firstname': contact_data.get('first_name', ''),
            'lastname': contact_data.get('last_name', ''),
            'phone': contact_data.get('phone', ''),
            'company': contact_data.get('company', ''),
            'message': contact_data.get('message', ''),
            'hs_lead_status': 'NEW',
        }

        # Nettoyer les valeurs vides
        properties = {k: v for k, v in properties.items() if v}

        payload = {'properties': properties}

        try:
            response = requests.post(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self._headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            contact = response.json()
            contact_id = contact.get('id')
            logger.info(f"Contact créé dans HubSpot: {contact_id}")
            return contact_id

        except requests.exceptions.RequestException as e:
            # HubSpot peut retourner 409 si contact existe déjà
            if hasattr(e, 'response') and e.response.status_code == 409:
                logger.info("Contact existe déjà dans HubSpot")
                return self._find_contact_by_email(contact_data.get('email', ''))
            logger.error(f"Erreur HubSpot: {e}")
            return None

    def _find_contact_by_email(self, email: str) -> Optional[str]:
        """Recherche un contact par email."""
        if not email:
            return None

        try:
            response = requests.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts/{email}",
                headers=self._headers(),
                params={'idProperty': 'email'},
                timeout=10
            )
            if response.ok:
                return response.json().get('id')
        except Exception:
            pass
        return None

    def create_deal(self, deal_data: Dict[str, Any], contact_id: Optional[str] = None) -> Optional[str]:
        """
        Crée une affaire (deal) dans HubSpot.

        Args:
            deal_data: Dictionnaire avec les infos de l'affaire
            contact_id: ID du contact à associer (optionnel)

        Returns:
            ID du deal HubSpot ou None si erreur
        """
        if not self.is_configured:
            return None

        properties = {
            'dealname': deal_data.get('name', 'Nouvelle opportunité'),
            'amount': deal_data.get('amount', ''),
            'dealstage': 'appointmentscheduled',  # Stage par défaut
            'pipeline': 'default',
        }

        # Nettoyer les valeurs vides
        properties = {k: v for k, v in properties.items() if v}

        payload = {'properties': properties}

        # Associer au contact si disponible
        if contact_id:
            payload['associations'] = [{
                'to': {'id': contact_id},
                'types': [{'associationCategory': 'HUBSPOT_DEFINED', 'associationTypeId': 3}]
            }]

        try:
            response = requests.post(
                f"{self.BASE_URL}/crm/v3/objects/deals",
                headers=self._headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            deal = response.json()
            deal_id = deal.get('id')
            logger.info(f"Deal créé dans HubSpot: {deal_id}")
            return deal_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur création deal HubSpot: {e}")
            return None


class CRMService:
    """
    Service unifié pour la synchronisation CRM.

    Utilise Airtable ou HubSpot selon la configuration disponible.
    """

    def __init__(self):
        self.airtable = AirtableService()
        self.hubspot = HubSpotService()

    @property
    def is_configured(self) -> bool:
        """Retourne True si au moins un CRM est configuré."""
        return self.airtable.is_configured or self.hubspot.is_configured

    def sync_lead(self, lead) -> Dict[str, Optional[str]]:
        """
        Synchronise un lead Django vers les CRM configurés.

        Args:
            lead: Instance de Lead (apps.leads.models.Lead)

        Returns:
            Dict avec les IDs créés dans chaque CRM
        """
        results = {
            'airtable_id': None,
            'hubspot_id': None,
        }

        # Préparer les données
        lead_data = {
            'name': getattr(lead, 'name', ''),
            'email': getattr(lead, 'email', ''),
            'phone': getattr(lead, 'phone', ''),
            'message': getattr(lead, 'message', ''),
            'company': getattr(lead, 'company', ''),
            'source': 'Website - Trait d\'Union Studio',
        }

        # Parser le nom pour HubSpot
        name_parts = lead_data['name'].split(' ', 1)
        lead_data['first_name'] = name_parts[0]
        lead_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''

        # Sync Airtable
        if self.airtable.is_configured:
            results['airtable_id'] = self.airtable.create_lead(lead_data)

        # Sync HubSpot
        if self.hubspot.is_configured:
            results['hubspot_id'] = self.hubspot.create_contact(lead_data)

        return results

    def sync_quote(self, quote) -> Dict[str, Optional[str]]:
        """
        Synchronise un devis vers HubSpot (comme Deal).

        Args:
            quote: Instance de Quote

        Returns:
            Dict avec l'ID du deal créé
        """
        results = {'hubspot_deal_id': None}

        if not self.hubspot.is_configured:
            return results

        # Créer ou retrouver le contact
        contact_id = None
        if quote.client:
            contact_data = {
                'email': quote.client.email,
                'first_name': quote.client.full_name.split()[0] if quote.client.full_name else '',
                'last_name': ' '.join(quote.client.full_name.split()[1:]) if quote.client.full_name else '',
                'phone': quote.client.phone,
                'company': getattr(quote.client, 'company', ''),
            }
            contact_id = self.hubspot.create_contact(contact_data)

        # Créer le deal
        deal_data = {
            'name': f"Devis {quote.number} - {quote.client.full_name if quote.client else 'Client'}",
            'amount': str(quote.total_ttc) if quote.total_ttc else '',
        }
        results['hubspot_deal_id'] = self.hubspot.create_deal(deal_data, contact_id)

        return results


# Instance singleton pour faciliter l'import
crm_service = CRMService()
