"""Recopie les médias de Cloudinary vers le stockage objet OVH (S3).

Parcourt tous les ``FileField`` / ``ImageField`` de tous les modèles et
transfère chaque fichier référencé. Le **nom stocké en base n'est jamais
modifié** : c'est ce qui rend la bascule sans risque et réversible. Une fois
les fichiers copiés, il suffit de définir les variables ``S3_*`` pour que
Django serve les mêmes chemins depuis OVH — et de retirer ces variables pour
revenir à Cloudinary si besoin.

À lancer **avant** la bascule, pendant que Cloudinary est encore actif :

    python manage.py migrate_media_to_s3 --dry-run   # inventaire
    python manage.py migrate_media_to_s3            # transfert

La commande est idempotente : un fichier déjà présent à destination est
ignoré, ce qui permet de la relancer autant de fois que nécessaire (reprise
après coupure réseau, ajout de nouveaux médias entre deux passes).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from dataclasses import field as dataclass_field

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import models

logger = logging.getLogger(__name__)


@dataclass
class Report:
    copied: int = 0
    skipped: int = 0
    missing: int = 0
    failed: int = 0
    errors: list[str] = dataclass_field(default_factory=list)


class Command(BaseCommand):
    help = "Recopie les médias de Cloudinary vers le stockage objet OVH (S3)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Inventorie les fichiers sans rien transférer.",
        )
        parser.add_argument(
            '--model', action='append', dest='models', default=None,
            metavar='app.Model',
            help="Limiter à ce modèle (répétable). Par défaut : tous.",
        )
        parser.add_argument(
            '--overwrite', action='store_true',
            help="Retransfère même si le fichier existe déjà à destination.",
        )
        parser.add_argument(
            '--limit', type=int, default=0,
            help="S'arrête après N fichiers transférés (test sur un échantillon).",
        )

    def handle(self, *args, **options) -> None:
        source = self._cloudinary_storage()
        destination = self._s3_storage()
        report = Report()

        targets = self._targets(options.get('models'))
        if not targets:
            raise CommandError('Aucun champ fichier à traiter.')

        self.stdout.write(
            f"{len(targets)} champ(s) fichier à parcourir"
            f"{' — DRY RUN' if options['dry_run'] else ''}\n"
        )

        for model, field_names in targets:
            self._migrate_model(
                model, field_names, source, destination, report, options,
            )
            if options['limit'] and report.copied >= options['limit']:
                self.stdout.write(self.style.WARNING(
                    f"\nLimite de {options['limit']} fichier(s) atteinte."
                ))
                break

        self._summarise(report, options['dry_run'])

    # ── Parcours ─────────────────────────────────────────────────
    def _targets(self, wanted: list[str] | None):
        """Modèles et champs fichiers à traiter, filtrés par --model."""
        wanted_lower = {w.lower() for w in wanted} if wanted else None
        targets = []
        for model in apps.get_models():
            if wanted_lower and model._meta.label.lower() not in wanted_lower:
                continue
            names = [
                f.name for f in model._meta.get_fields()
                if isinstance(f, models.FileField)
            ]
            if names:
                targets.append((model, names))

        if wanted_lower and not targets:
            raise CommandError(f"Modèle(s) introuvable(s) : {', '.join(wanted)}")
        return targets

    def _migrate_model(self, model, field_names, source, destination,
                       report, options) -> None:
        label = model._meta.label
        # Ne charger que les lignes ayant au moins un fichier renseigné.
        query = models.Q()
        for name in field_names:
            query |= ~models.Q(**{name: ''}) & models.Q(**{f'{name}__isnull': False})

        queryset = model._default_manager.filter(query).only('pk', *field_names)
        total = queryset.count()
        if not total:
            return

        self.stdout.write(f"{label} ({', '.join(field_names)}) — {total} ligne(s)")

        for instance in queryset.iterator(chunk_size=100):
            for name in field_names:
                file_field = getattr(instance, name, None)
                stored_name = getattr(file_field, 'name', '') or ''
                if not stored_name:
                    continue
                self._transfer(
                    stored_name, source, destination, report, options,
                    origin=f'{label}#{instance.pk}.{name}',
                )
                if options['limit'] and report.copied >= options['limit']:
                    return

    def _transfer(self, name, source, destination, report, options,
                  *, origin: str) -> None:
        """Transfère un fichier en conservant son chemin exact."""
        try:
            if not options['overwrite'] and destination.exists(name):
                report.skipped += 1
                return
        except Exception as exc:  # noqa: BLE001 - backend S3 injoignable
            report.failed += 1
            report.errors.append(f'{origin}: destination illisible ({exc})')
            return

        if options['dry_run']:
            report.copied += 1
            self.stdout.write(f"  + {name}")
            return

        try:
            payload = self._read(source, name)
        except FileNotFoundError:
            # Référence en base sans fichier derrière : fréquent après des
            # suppressions manuelles côté Cloudinary. On le signale sans
            # interrompre la migration.
            report.missing += 1
            report.errors.append(f'{origin}: absent de la source ({name})')
            return
        except Exception as exc:  # noqa: BLE001
            report.failed += 1
            report.errors.append(f'{origin}: lecture impossible ({exc})')
            return

        try:
            destination.save(name, ContentFile(payload))
        except Exception as exc:  # noqa: BLE001
            report.failed += 1
            report.errors.append(f'{origin}: écriture impossible ({exc})')
            return

        report.copied += 1
        self.stdout.write(f"  → {name} ({len(payload) / 1024:.0f} Ko)")

    def _read(self, source, name: str) -> bytes:
        """Lit le fichier source, par le backend puis par HTTP en secours.

        ``MediaCloudinaryStorage`` n'implémente pas toujours ``open()`` de
        façon fiable ; l'URL publique, elle, fonctionne toujours.
        """
        try:
            with source.open(name) as handle:
                payload = handle.read()
            if payload:
                return payload
        except FileNotFoundError:
            raise
        except Exception as exc:  # noqa: BLE001 - on tente l'URL publique
            logger.debug('open() indisponible pour %s (%s) — repli HTTP', name, exc)

        import requests

        url = source.url(name)
        response = requests.get(url, timeout=60)
        if response.status_code == 404:
            raise FileNotFoundError(name)
        response.raise_for_status()
        return response.content

    # ── Backends ─────────────────────────────────────────────────
    def _cloudinary_storage(self):
        try:
            from cloudinary_storage.storage import MediaCloudinaryStorage
        except ImportError as exc:
            raise CommandError(
                "django-cloudinary-storage est requis comme source. "
                "Lancer cette commande avant de retirer Cloudinary."
            ) from exc
        return MediaCloudinaryStorage()

    def _s3_storage(self):
        from django.conf import settings

        if not getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''):
            raise CommandError(
                "Destination non configurée : définir S3_BUCKET_NAME, "
                "S3_ENDPOINT_URL, S3_ACCESS_KEY_ID et S3_SECRET_ACCESS_KEY."
            )
        try:
            from storages.backends.s3 import S3Storage
        except ImportError as exc:
            raise CommandError('django-storages est requis.') from exc
        return S3Storage()

    # ── Sortie ───────────────────────────────────────────────────
    def _summarise(self, report: Report, dry_run: bool) -> None:
        verb = 'à transférer' if dry_run else 'transféré(s)'
        self.stdout.write('')
        self.stdout.write(f"  {report.copied} fichier(s) {verb}")
        self.stdout.write(f"  {report.skipped} déjà présent(s) à destination")
        if report.missing:
            self.stdout.write(self.style.WARNING(
                f"  {report.missing} référence(s) sans fichier source"
            ))
        if report.failed:
            self.stdout.write(self.style.ERROR(f"  {report.failed} échec(s)"))

        for line in report.errors[:20]:
            self.stdout.write(f"    - {line}")
        if len(report.errors) > 20:
            self.stdout.write(f"    … et {len(report.errors) - 20} autre(s)")

        if report.failed:
            raise CommandError(
                'Migration incomplète : corriger les échecs puis relancer '
                '(la commande est idempotente).'
            )
        self.stdout.write(self.style.SUCCESS('\nMigration des médias terminée.'))
