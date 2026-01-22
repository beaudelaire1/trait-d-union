"""Management command to populate default email templates."""
from django.core.management.base import BaseCommand
from apps.leads.email_models import EmailTemplate, EmailTemplateCategory


class Command(BaseCommand):
    help = 'Populate database with default email templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Prospection initiale',
                'category': EmailTemplateCategory.PROSPECTION,
                'subject': 'Découvrez comment Trait d\'Union Studio peut transformer votre présence digitale',
                'body_html': '''
<p>Bonjour,</p>

<p>Je me permets de vous contacter car <strong>Trait d'Union Studio</strong> accompagne des entreprises comme la vôtre dans leur transformation digitale.</p>

<p>Nous sommes spécialisés dans :</p>
<ul>
    <li>La création de sites web sur-mesure et performants</li>
    <li>Le développement de plateformes e-commerce</li>
    <li>La conception d'applications web innovantes</li>
</ul>

<p>J'aimerais échanger avec vous sur vos projets digitaux et voir comment nous pourrions vous accompagner.</p>

<p>Seriez-vous disponible pour un appel découverte de 15 minutes cette semaine ?</p>

<p>Cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Remerciement après rendez-vous',
                'category': EmailTemplateCategory.REMERCIEMENT,
                'subject': 'Merci pour votre temps - Trait d\'Union Studio',
                'body_html': '''
<p>Bonjour,</p>

<p>Je tenais à vous remercier pour le temps que vous nous avez accordé lors de notre échange.</p>

<p>Comme évoqué, voici un <strong>récapitulatif de nos échanges</strong> :</p>
<ul>
    <li>Votre projet : [détails du projet]</li>
    <li>Vos objectifs : [objectifs clés]</li>
    <li>Nos recommandations : [recommandations]</li>
</ul>

<p>Nous sommes ravis de pouvoir vous accompagner dans ce projet ambitieux.</p>

<p>N'hésitez pas si vous avez la moindre question !</p>

<p>À très bientôt,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Relance douce',
                'category': EmailTemplateCategory.RELANCE,
                'subject': 'Re: Votre projet digital',
                'body_html': '''
<p>Bonjour,</p>

<p>Je me permets de revenir vers vous concernant notre dernier échange au sujet de votre projet digital.</p>

<p>Avez-vous eu l'occasion d'examiner notre proposition ? Je reste à votre disposition pour toute question ou clarification.</p>

<p>Si le moment n'est pas opportun, n'hésitez pas à me le faire savoir, nous pourrons en reparler ultérieurement.</p>

<p>Cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Relance proposition commerciale',
                'category': EmailTemplateCategory.RELANCE,
                'subject': 'Relance - Proposition commerciale Trait d\'Union Studio',
                'body_html': '''
<p>Bonjour,</p>

<p>Je reviens vers vous concernant la <strong>proposition commerciale</strong> que nous vous avons transmise le [date].</p>

<p><strong>Points clés de notre offre :</strong></p>
<ul>
    <li>Solution sur-mesure adaptée à vos besoins</li>
    <li>Accompagnement personnalisé de A à Z</li>
    <li>Technologies modernes et performantes</li>
    <li>Délais et budget maîtrisés</li>
</ul>

<p>Avez-vous besoin de précisions supplémentaires ? Je serais ravi d'organiser un point téléphonique pour répondre à vos questions.</p>

<p>Bien cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Proposition commerciale',
                'category': EmailTemplateCategory.PROPOSITION,
                'subject': 'Votre proposition commerciale - Trait d\'Union Studio',
                'body_html': '''
<p>Bonjour,</p>

<p>Suite à nos échanges, j'ai le plaisir de vous transmettre notre <strong>proposition commerciale</strong> pour votre projet.</p>

<p><strong>Résumé de l'offre :</strong></p>
<ul>
    <li>Prestation : [description]</li>
    <li>Délai de réalisation : [durée]</li>
    <li>Investissement : [montant]</li>
</ul>

<p>Cette proposition a été élaborée spécifiquement pour répondre à vos besoins et objectifs.</p>

<p>Je reste à votre entière disposition pour toute question ou ajustement.</p>

<p>Au plaisir d'avancer ensemble sur ce projet !</p>

<p>Cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Confirmation de rendez-vous',
                'category': EmailTemplateCategory.CONFIRMATION,
                'subject': 'Confirmation de rendez-vous - Trait d\'Union Studio',
                'body_html': '''
<p>Bonjour,</p>

<p>Je vous confirme notre <strong>rendez-vous</strong> :</p>

<p><strong>📅 Date et heure :</strong> [date et heure]<br>
<strong>📍 Lieu :</strong> [lieu ou lien visioconférence]<br>
<strong>⏱️ Durée estimée :</strong> [durée]</p>

<p><strong>Ordre du jour :</strong></p>
<ul>
    <li>[Point 1]</li>
    <li>[Point 2]</li>
    <li>[Point 3]</li>
</ul>

<p>Si vous avez besoin de modifier ce créneau, n'hésitez pas à me le faire savoir.</p>

<p>À très bientôt !</p>

<p>Cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
            {
                'name': 'Suivi de projet - Avancement',
                'category': EmailTemplateCategory.SUIVI,
                'subject': 'Point d\'avancement - Votre projet',
                'body_html': '''
<p>Bonjour,</p>

<p>Voici un <strong>point d'avancement</strong> sur votre projet :</p>

<p><strong>✅ Réalisé cette semaine :</strong></p>
<ul>
    <li>[Tâche 1 complétée]</li>
    <li>[Tâche 2 complétée]</li>
</ul>

<p><strong>🚧 En cours :</strong></p>
<ul>
    <li>[Tâche en cours]</li>
</ul>

<p><strong>📅 Prochaines étapes :</strong></p>
<ul>
    <li>[Prochaine étape 1]</li>
    <li>[Prochaine étape 2]</li>
</ul>

<p>Le projet avance comme prévu et nous restons dans les temps.</p>

<p>N'hésitez pas si vous avez des questions !</p>

<p>Cordialement,<br>
L'équipe Trait d'Union Studio</p>
                '''
            },
        ]

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                category=template_data['category'],
                defaults={
                    'subject': template_data['subject'],
                    'body_html': template_data['body_html'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Template créé: {template.name}')
                )
            else:
                # Update if exists
                template.subject = template_data['subject']
                template.body_html = template_data['body_html']
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Template mis à jour: {template.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Terminé! {created_count} templates créés, {updated_count} mis à jour'
            )
        )
