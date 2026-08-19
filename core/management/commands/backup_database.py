"""Sauvegarde la base PostgreSQL vers un stockage objet S3 (OVH).

Sur Render, la base managée était sauvegardée quotidiennement par la
plateforme. En auto-hébergeant PostgreSQL dans un conteneur sur le VPS, cette
garantie disparaît : cette commande la remplace.

Le dump est produit au format ``custom`` de pg_dump (compressé, restaurable
sélectivement via ``pg_restore``), chiffré si ``BACKUP_ENCRYPTION_KEY`` est
défini, puis poussé vers le stockage objet. Les sauvegardes plus anciennes que
la rétention sont supprimées.

Planifié via une tâche planifiée Coolify (voir deploy/README.md) :

    python manage.py backup_database

Restauration : voir deploy/README.md, section « Restaurer une sauvegarde ».
"""
from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DEFAULT_PREFIX = 'postgres/'
DEFAULT_RETENTION_DAYS = 30

# nom : traitdunion-2026-08-19T14-30-00Z.dump[.enc]
_BACKUP_RE = re.compile(
    r'^(?P<db>.+)-(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z)\.dump(\.enc)?$'
)


class Command(BaseCommand):
    help = "Sauvegarde PostgreSQL vers le stockage objet S3 (OVH)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--bucket',
            default=os.environ.get('BACKUP_S3_BUCKET') or '',
            help="Bucket de destination (défaut : BACKUP_S3_BUCKET, sinon S3_BUCKET_NAME).",
        )
        parser.add_argument(
            '--prefix',
            default=os.environ.get('BACKUP_S3_PREFIX', DEFAULT_PREFIX),
            help=f"Préfixe des objets (défaut « {DEFAULT_PREFIX} »).",
        )
        parser.add_argument(
            '--retention-days', type=int,
            default=int(os.environ.get('BACKUP_RETENTION_DAYS', DEFAULT_RETENTION_DAYS)),
            help=f"Supprime les sauvegardes plus anciennes (défaut {DEFAULT_RETENTION_DAYS} j).",
        )
        parser.add_argument(
            '--keep-local', action='store_true',
            help="Conserve le fichier local (débogage).",
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Produit le dump sans l'envoyer ni purger quoi que ce soit.",
        )

    # ── Entrée ───────────────────────────────────────────────────
    def handle(self, *args, **options) -> None:
        bucket = options['bucket'] or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
        if not bucket and not options['dry_run']:
            raise CommandError(
                "Aucun bucket de destination : définir BACKUP_S3_BUCKET "
                "(ou S3_BUCKET_NAME), ou utiliser --dry-run."
            )

        db = settings.DATABASES['default']
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
        name = f"{db.get('NAME') or 'database'}-{stamp}.dump"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            self._pg_dump(db, path)

            key_material = os.environ.get('BACKUP_ENCRYPTION_KEY')
            if key_material:
                path = self._encrypt(path, key_material)
            else:
                self.stdout.write(self.style.WARNING(
                    "BACKUP_ENCRYPTION_KEY absent — sauvegarde envoyée en clair. "
                    "La base contient des données personnelles (leads, devis, "
                    "factures) : définir cette variable est vivement conseillé."
                ))

            size_mb = path.stat().st_size / 1_048_576
            self.stdout.write(f"Dump prêt : {path.name} ({size_mb:.1f} Mo)")

            if options['dry_run']:
                self.stdout.write(self.style.WARNING('--dry-run : aucun envoi.'))
                if options['keep_local']:
                    self._keep_local(path)
                return

            self._upload(path, bucket, options['prefix'])
            if options['keep_local']:
                self._keep_local(path)

        removed = self._prune(bucket, options['prefix'], options['retention_days'])
        self.stdout.write(self.style.SUCCESS(
            f"Sauvegarde terminée ({removed} ancienne(s) supprimée(s))."
        ))

    # ── Étapes ───────────────────────────────────────────────────
    def _pg_dump(self, db: dict, path: Path) -> None:
        """Produit le dump. Le mot de passe passe par l'environnement.

        Le format ``custom`` (-Fc) est compressé et permet une restauration
        sélective, table par table, avec pg_restore.
        """
        engine = db.get('ENGINE', '')
        if 'postgresql' not in engine:
            raise CommandError(
                f"Base non PostgreSQL ({engine}) : sauvegarde non supportée."
            )

        cmd = ['pg_dump', '--format=custom', '--no-owner', '--no-privileges',
               '--file', str(path)]
        env = os.environ.copy()

        # Django expose l'URL éclatée ; on reconstruit les options pg_dump.
        if db.get('HOST'):
            cmd += ['--host', db['HOST']]
        if db.get('PORT'):
            cmd += ['--port', str(db['PORT'])]
        if db.get('USER'):
            cmd += ['--username', db['USER']]
        if db.get('PASSWORD'):
            env['PGPASSWORD'] = db['PASSWORD']
        cmd.append(db['NAME'])

        self.stdout.write(f"pg_dump → {db.get('HOST') or 'local'}/{db['NAME']}…")
        try:
            proc = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=3600,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CommandError(
                "pg_dump introuvable — le paquet postgresql-client doit être "
                "installé dans l'image (voir Dockerfile)."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CommandError('pg_dump : délai dépassé (1 h).') from exc

        if proc.returncode != 0:
            raise CommandError(f"pg_dump a échoué : {proc.stderr.strip()[:500]}")

    def _encrypt(self, path: Path, key_material: str) -> Path:
        """Chiffre le dump en AES-256 via openssl (dérivation PBKDF2)."""
        target = path.with_suffix(path.suffix + '.enc')
        env = os.environ.copy()
        env['BACKUP_PASSPHRASE'] = key_material
        try:
            proc = subprocess.run(
                ['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', '200000',
                 '-salt', '-in', str(path), '-out', str(target),
                 '-pass', 'env:BACKUP_PASSPHRASE'],
                env=env, capture_output=True, text=True, timeout=1800,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CommandError("openssl introuvable dans l'image.") from exc

        if proc.returncode != 0:
            raise CommandError(f"Chiffrement échoué : {proc.stderr.strip()[:500]}")

        path.unlink(missing_ok=True)
        return target

    def _upload(self, path: Path, bucket: str, prefix: str) -> None:
        client = self._s3_client()
        key = f"{prefix.rstrip('/')}/{path.name}" if prefix else path.name
        self.stdout.write(f"Envoi → s3://{bucket}/{key}…")
        client.upload_file(str(path), bucket, key)

    def _prune(self, bucket: str, prefix: str, retention_days: int) -> int:
        """Supprime les sauvegardes dont l'horodatage dépasse la rétention.

        On se fie à l'horodatage du nom plutôt qu'à ``LastModified`` : ce
        dernier changerait si un objet était recopié, ce qui prolongerait
        silencieusement la rétention.
        """
        if retention_days <= 0:
            return 0

        client = self._s3_client()
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=retention_days)
        removed = 0

        paginator = client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                name = obj['Key'].rsplit('/', 1)[-1]
                match = _BACKUP_RE.match(name)
                if not match:
                    continue
                created = dt.datetime.strptime(
                    match.group('stamp'), '%Y-%m-%dT%H-%M-%SZ'
                ).replace(tzinfo=dt.timezone.utc)
                if created < cutoff:
                    client.delete_object(Bucket=bucket, Key=obj['Key'])
                    removed += 1
                    self.stdout.write(f"  purge : {obj['Key']}")
        return removed

    # ── Utilitaires ──────────────────────────────────────────────
    def _s3_client(self):
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - dépendance déclarée
            raise CommandError('boto3 est requis pour la sauvegarde.') from exc

        endpoint = os.environ.get('BACKUP_S3_ENDPOINT_URL') or getattr(
            settings, 'AWS_S3_ENDPOINT_URL', None
        )
        return boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=(os.environ.get('BACKUP_S3_ACCESS_KEY_ID')
                               or getattr(settings, 'AWS_ACCESS_KEY_ID', None)),
            aws_secret_access_key=(os.environ.get('BACKUP_S3_SECRET_ACCESS_KEY')
                                   or getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)),
            region_name=(os.environ.get('BACKUP_S3_REGION_NAME')
                         or getattr(settings, 'AWS_S3_REGION_NAME', 'gra')),
        )

    def _keep_local(self, path: Path) -> None:
        target = Path(settings.BASE_DIR) / path.name
        target.write_bytes(path.read_bytes())
        self.stdout.write(f"Copie locale conservée : {target}")
