"""App pour la gestion des devis.

Cette application remplace l'ancienne app ``quotes`` et gère les demandes de
devis des clients.  Elle stocke les informations de contact ainsi que le
service souhaité et fournit un point d'entrée pour convertir la demande en
facture ultérieurement.  Les champs de base (nom, email, téléphone, service,
message) sont conservés pour rester simples mais pourront être étendus avec
des tables ``Client`` et ``QuoteItem`` selon le cahier des charges.
"""