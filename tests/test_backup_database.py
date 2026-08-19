"""Tests de la commande de sauvegarde PostgreSQL vers le stockage objet.

En auto-hébergeant PostgreSQL (VPS OVH + Coolify), les sauvegardes ne sont plus
fournies par la plateforme : cette commande devient le seul filet. Sa logique
de rétention est testée en priorité — une purge trop agressive détruirait les
sauvegardes qu'elle est censée protéger.
"""
from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.management.commands.backup_database import Command


def _stamp(days_ago: int) -> str:
    moment = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days_ago)
    return moment.strftime('%Y-%m-%dT%H-%M-%SZ')


def _fake_client(keys: list[str]) -> MagicMock:
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {'Contents': [{'Key': key} for key in keys]}
    ]
    client.get_paginator.return_value = paginator
    return client


class TestRetention:
    def _prune(self, keys, retention_days=30):
        client = _fake_client(keys)
        command = Command()
        with patch.object(Command, '_s3_client', return_value=client):
            removed = command._prune('bucket', 'postgres/', retention_days)
        deleted = [
            call.kwargs['Key'] for call in client.delete_object.call_args_list
        ]
        return removed, deleted

    def test_deletes_only_backups_past_retention(self):
        keys = [
            f'postgres/traitdunion-{_stamp(1)}.dump',    # récent → gardé
            f'postgres/traitdunion-{_stamp(29)}.dump',   # dans la fenêtre
            f'postgres/traitdunion-{_stamp(31)}.dump',   # expiré
            f'postgres/traitdunion-{_stamp(400)}.dump',  # expiré
        ]
        removed, deleted = self._prune(keys, retention_days=30)

        assert removed == 2
        assert all(_stamp(1) not in key and _stamp(29) not in key for key in deleted)

    def test_encrypted_backups_are_recognised(self):
        keys = [f'postgres/traitdunion-{_stamp(90)}.dump.enc']
        removed, deleted = self._prune(keys, retention_days=30)

        assert removed == 1, 'les .dump.enc doivent aussi être purgés'
        assert deleted == keys

    def test_unrelated_objects_are_never_touched(self):
        """Un objet étranger au préfixe ne doit jamais être supprimé."""
        keys = [
            'postgres/notes-importantes.txt',
            'postgres/traitdunion.dump',            # pas d'horodatage
            'postgres/media-backup-2020.tar.gz',
        ]
        removed, deleted = self._prune(keys, retention_days=1)

        assert removed == 0
        assert deleted == []

    def test_retention_zero_disables_pruning(self):
        keys = [f'postgres/traitdunion-{_stamp(999)}.dump']
        removed, deleted = self._prune(keys, retention_days=0)

        assert removed == 0
        assert deleted == []


class TestGuards:
    def test_refuses_non_postgres_database(self):
        """La suite de tests tourne sur SQLite : le refus doit être explicite."""
        with pytest.raises(CommandError, match='PostgreSQL'):
            call_command('backup_database', '--dry-run')

    def test_requires_a_destination_bucket(self):
        with patch.object(Command, '_pg_dump'), \
             patch('django.conf.settings.AWS_STORAGE_BUCKET_NAME', '', create=True):
            with pytest.raises(CommandError, match='bucket'):
                call_command('backup_database', '--bucket', '')
