"""Tests de la migration des médias Cloudinary → OVH Object Storage.

Le point critique : le chemin stocké en base ne doit jamais changer. C'est ce
qui rend la bascule réversible — il suffit d'ajouter ou de retirer les
variables S3_* pour passer d'un stockage à l'autre.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.chroniques.models import Article
from core.management.commands.migrate_media_to_s3 import Command


@pytest.fixture
def storages():
    """Remplace les deux backends par des doubles contrôlables."""
    source = MagicMock()
    destination = MagicMock()
    destination.exists.return_value = False
    with patch.object(Command, '_cloudinary_storage', return_value=source), \
         patch.object(Command, '_s3_storage', return_value=destination):
        yield source, destination


def _read_returns(source, payload: bytes):
    handle = MagicMock()
    handle.read.return_value = payload
    source.open.return_value.__enter__.return_value = handle


@pytest.mark.django_db
class TestMediaMigration:
    def _article(self, cover='chroniques/couverture.jpg'):
        return Article.objects.create(
            title='Chronique test',
            slug='chronique-test',
            cover_image=cover,
        )

    def test_preserves_the_stored_path(self, storages):
        """Le nom écrit à destination est identique à celui de la base."""
        source, destination = storages
        article = self._article('chroniques/couverture.jpg')
        _read_returns(source, b'imagedata')

        call_command('migrate_media_to_s3', '--model', 'chroniques.Article')

        destination.save.assert_called_once()
        written_name = destination.save.call_args.args[0]
        assert written_name == 'chroniques/couverture.jpg'

        article.refresh_from_db()
        assert article.cover_image.name == 'chroniques/couverture.jpg', (
            'la migration ne doit pas toucher la base'
        )

    def test_dry_run_transfers_nothing(self, storages):
        source, destination = storages
        self._article()
        _read_returns(source, b'imagedata')

        call_command('migrate_media_to_s3', '--dry-run',
                     '--model', 'chroniques.Article')

        destination.save.assert_not_called()
        source.open.assert_not_called()

    def test_existing_destination_file_is_skipped(self, storages):
        """Idempotence : relancer la commande ne retransfère rien."""
        source, destination = storages
        destination.exists.return_value = True
        self._article()

        call_command('migrate_media_to_s3', '--model', 'chroniques.Article')

        destination.save.assert_not_called()

    def test_overwrite_forces_the_transfer(self, storages):
        source, destination = storages
        destination.exists.return_value = True
        self._article()
        _read_returns(source, b'imagedata')

        call_command('migrate_media_to_s3', '--overwrite',
                     '--model', 'chroniques.Article')

        destination.save.assert_called_once()

    def test_missing_source_file_does_not_abort_the_run(self, storages):
        """Une référence orpheline est signalée, pas fatale."""
        source, destination = storages
        self._article()
        source.open.side_effect = FileNotFoundError('absent')
        source.url.return_value = 'https://res.cloudinary.com/demo/absent.jpg'

        # Ne lève pas : les orphelins ne sont pas des échecs.
        call_command('migrate_media_to_s3', '--model', 'chroniques.Article')
        destination.save.assert_not_called()

    def test_write_failure_is_reported_as_an_error(self, storages):
        source, destination = storages
        self._article()
        _read_returns(source, b'imagedata')
        destination.save.side_effect = OSError('bucket plein')

        with pytest.raises(CommandError, match='incomplète'):
            call_command('migrate_media_to_s3', '--model', 'chroniques.Article')

    def test_rows_without_files_are_ignored(self, storages):
        source, destination = storages
        Article.objects.create(title='Sans image', slug='sans-image')

        call_command('migrate_media_to_s3', '--model', 'chroniques.Article')

        destination.save.assert_not_called()

    def test_unknown_model_is_rejected(self, storages):
        with pytest.raises(CommandError, match='introuvable'):
            call_command('migrate_media_to_s3', '--model', 'inexistant.Modele')
