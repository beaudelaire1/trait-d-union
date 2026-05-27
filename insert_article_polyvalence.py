"""Insertion de l'article 'Trop polyvalent pour être bon' dans les Chroniques TUS.

Usage :
    DATABASE_URL="postgres://..." python insert_article_polyvalence.py
"""
import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.chroniques.models import Article, Category  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()


TITLE = "Trop polyvalent pour être bon"
SUBTITLE = (
    "Quand la TPE/PME transforme son expert en généraliste : "
    "le coût silencieux de la dispersion"
)
CATEGORY_NAME = "Organisations"
CATEGORY_SLUG = "organisations"
EXCERPT = (
    "Pourquoi exiger d'un collaborateur qu'il sache tout faire revient, à terme, "
    "à s'assurer qu'il ne fasse plus rien vraiment bien — et comment cette dérive, "
    "lente et silencieuse, ronge la valeur produite par l'entreprise sans jamais "
    "apparaître dans aucun tableau de bord."
)
META_DESCRIPTION = (
    "Polyvalence, dispersion, dilution de l'expertise : pourquoi transformer un "
    "spécialiste en homme-orchestre coûte plus cher qu'il n'y paraît aux TPE/PME."
)

BODY = """Il existe dans la vie des TPE et des PME une figure familière, presque attachante : celle du collaborateur qui *sait tout faire*. Celui que l'on sollicite parce qu'il dépanne, parce qu'il accepte, parce qu'il ne dit jamais non, parce qu'il s'est rendu — au fil des mois — indispensable précisément par sa capacité à intervenir partout. Cette figure n'est pas, à l'origine, le produit d'une stratégie. Elle est le résultat d'une accumulation : une urgence un jour, un dépannage la semaine suivante, une mission qui s'éternise parce qu'elle marche, et l'on s'aperçoit, deux ans plus tard, que celui qui avait été recruté pour une expertise précise est devenu un homme-orchestre dont plus personne — y compris lui-même — ne saurait décrire précisément le poste.

Cette dérive est l'une des plus répandues, et l'une des moins nommées, du fonctionnement quotidien des petites organisations. Elle a un nom managérial poli — la **polyvalence** — qui en masque la nature réelle : *la dispersion*. Cet article examine les mécanismes par lesquels une compétence rare se transforme en compétence diluée, les effets concrets de cette dilution sur la performance individuelle et collective, et les conditions dans lesquelles une organisation peut restituer à ses experts l'espace dont ils ont besoin pour le rester.

## I. La promesse trompeuse de la polyvalence

La polyvalence jouit, dans la culture managériale des petites structures, d'un prestige rarement discuté. Elle est associée à la souplesse, à la débrouillardise, à cette capacité d'adaptation qui distingue — dit-on — la PME agile du grand groupe rigide. Un collaborateur polyvalent est, dans cet imaginaire, un actif supérieur à un spécialiste : il couvre plus de surface, il pallie les absences, il évite à l'entreprise d'avoir à embaucher pour chaque besoin marginal.

Cette promesse n'est pas entièrement fausse. Dans les phases de démarrage, dans les périodes de tension de trésorerie, dans les organisations à effectif réduit, la polyvalence est une condition de survie. Une PME de cinq personnes n'a pas le luxe de la spécialisation stricte, et c'est précisément cette plasticité qui lui permet, certaines années, d'absorber des variations de charge qu'une organisation plus rigide aurait dû refuser.

Mais cette promesse a une face cachée que le discours managérial évoque rarement. La polyvalence n'est utile, sur le long terme, que dans la mesure où elle reste *adossée à une expertise principale*. Dès lors que les missions périphériques colonisent le temps de l'expert au point d'empêcher l'entretien de son cœur de compétence, le calcul s'inverse silencieusement : **l'entreprise croit gagner de la surface, elle perd de la profondeur**. Et la profondeur, dans les métiers où elle compte, est précisément ce qui distingue un livrable acceptable d'un livrable défendable, une réponse standard d'une réponse pertinente, une prestation moyenne d'une prestation que le client recommandera.

## II. La dilution de l'expertise n'est pas un événement, c'est une trajectoire

Personne ne décide, un matin, de transformer son meilleur spécialiste en généraliste fatigué. La dilution opère par micro-décisions, chacune raisonnable prise isolément, dont la somme produit pourtant une bascule structurelle.

Cela commence par une demande légitime : *« Tu peux jeter un œil à ça, c'est ton domaine connexe. »* Puis par une autre, quelques semaines plus tard, parce que personne d'autre n'est disponible. Puis une troisième, parce qu'il s'en est bien sorti la fois précédente. Au bout de six mois, ces tâches périphériques ne sont plus exceptionnelles : elles ont colonisé les créneaux qui servaient — autrefois — à la veille, à la formation continue, à la lecture des publications du secteur, à l'expérimentation technique, à toutes ces activités sans livrable immédiat qui constituent pourtant le substrat invisible de l'expertise.

Ce processus a une caractéristique redoutable : il est invisible dans les indicateurs de court terme. L'expert continue à produire, ses dossiers sortent, les clients ne se plaignent pas. Ce qui s'érode, c'est sa marge d'avance — cet écart entre ce qu'il sait et ce que sait le marché, qui constituait la véritable valeur que l'entreprise vendait sans toujours en avoir conscience. Cet écart se mesure non pas en mois, mais en années ; et lorsqu'il devient visible, il est généralement trop tard pour le rattraper sans rupture.

L'expertise est une grandeur **cumulative et périssable**. Cumulative parce qu'elle se construit par accumulation d'heures consacrées à un domaine précis ; périssable parce qu'elle se déprécie dès lors que cette accumulation s'interrompt, dans un environnement technique où le savoir de référence évolue continûment. Un expert qu'on disperse ne perd pas son expertise d'un coup. Il cesse simplement de l'entretenir — et la dépréciation fait, lentement, le reste.

## III. Ce que le client achète, et ce qu'il reçoit

Lorsqu'un client choisit une TPE ou une PME plutôt qu'un grand cabinet, il fait — consciemment ou non — un pari précis : il accepte de payer pour une expertise concentrée, identifiée, accessible, en échange d'une renonciation à la surface de service qu'une grande structure offrirait. Ce pari n'est pas seulement commercial ; il est structurellement constitutif de la valeur que la petite structure peut prétendre vendre.

Le problème survient lorsque l'entreprise, par le mouvement décrit plus haut, transforme intérieurement ce qu'elle continue à vendre extérieurement. Le client paie une expertise ; il reçoit une polyvalence. Le client a choisi un spécialiste ; il se retrouve face à un généraliste correct. L'écart entre la promesse commerciale et la réalité opérationnelle ne se manifeste pas, dans un premier temps, par une rupture brutale : il se manifeste par une lente érosion de la différence perçue entre cette PME et n'importe quelle autre. Et lorsque la différence perçue s'érode, **le seul critère de choix qui survit est le prix**. C'est le moment où la PME, sans comprendre pourquoi, voit ses marges se resserrer, ses arbitrages se durcir, ses meilleurs clients renégocier — alors même qu'elle estime, en interne, que la qualité de son travail n'a pas changé.

Elle n'a pas changé en effet : *c'est sa singularité qui a changé*. Une singularité diluée est une banalité en formation.

## IV. Le coût invisible inscrit dans l'organisation

La dispersion de l'expert ne coûte pas qu'au client et à l'expert lui-même. Elle inscrit, dans l'organisation toute entière, un ensemble de coûts diffus que la comptabilité analytique ne sait pas capter et que le dirigeant ne mesure, le plus souvent, qu'après leur cristallisation.

Le premier de ces coûts est le **coût de commutation**. Chaque fois qu'un expert passe d'un domaine où il est compétent à un domaine où il l'est moins, il paie un impôt cognitif — sous forme de temps de reprise, d'erreurs de débutant, de prudence excessive qui ralentit l'exécution. Cet impôt, individuellement modeste, devient massif à l'échelle d'une semaine de travail fractionnée en six chantiers hétérogènes. La productivité affichée se maintient ; la productivité réelle, mesurée en valeur produite par heure, s'effondre.

Le deuxième est le **coût d'opportunité de l'absence d'apprentissage**. Un expert qui travaille au sommet de sa compétence apprend de chaque dossier ; il consolide, il affine, il enrichit sa pratique. Un expert dispersé exécute, mais n'apprend plus — ou apprend des fragments hétérogènes qui ne se composent en aucune progression cumulative. L'entreprise paie un salaire de spécialiste pour une trajectoire de stagnation.

Le troisième est le **coût de transmission**. Une expertise concentrée est documentable, transmissible, formable. Une compétence diluée à travers vingt domaines ne l'est pas : elle existe dans la tête d'une seule personne, sous forme de bricolages contextuels que personne — pas même l'intéressé — ne saurait formaliser. L'organisation devient prisonnière des individus qu'elle a dispersés : leur départ devient une catastrophe non parce qu'ils étaient irremplaçables comme experts, mais parce qu'ils étaient devenus irremplaçables comme bricoleurs.

Le quatrième, le plus pernicieux, est le **coût d'identité**. Un expert dispersé perd progressivement la capacité à se présenter — à un client, à un partenaire, à un futur employeur — comme spécialiste de quelque chose. Cette perte est rarement formulée ; elle est ressentie comme un malaise, une lassitude, un sentiment de ne plus savoir précisément ce que l'on fait. Les départs qui s'ensuivent ne sont jamais attribués à leur cause réelle. Ils sont mis sur le compte de la rémunération, du climat, de l'envie d'ailleurs. Ils étaient, en réalité, la conséquence prévisible d'un usage qui avait dissous l'identité professionnelle de celui qui les portait.

> *« L'expertise est une grandeur cumulative et périssable. Une entreprise qui disperse ses experts n'économise pas sur l'embauche : elle dilapide, en silence, le capital cognitif qui justifiait ses prix. »*

## V. Les raisons rationnelles d'une dérive irrationnelle

Si la dispersion des experts est si coûteuse, pourquoi est-elle si répandue ? Parce qu'elle est, à chaque instant, **localement rationnelle**.

Pour le dirigeant qui doit traiter une demande urgente, recourir à l'expert disponible est *toujours* plus rapide que de chercher la ressource adéquate, de négocier sa disponibilité, ou de refuser la mission. Pour le collaborateur sollicité, accepter est toujours plus simple que de négocier le périmètre de son poste, surtout dans une organisation où la culture implicite valorise la disponibilité. Pour le client, demander à son interlocuteur habituel d'élargir sa prestation est toujours plus confortable que de s'adresser à un autre prestataire.

Ces trois rationalités locales se composent en **une déraison globale** : chacun, en optimisant son propre calcul de court terme, contribue à un résultat collectif que personne ne souhaiterait s'il en mesurait les effets à trois ans. C'est la signature des dérives organisationnelles les plus difficiles à corriger — non parce qu'elles seraient mystérieuses, mais parce que chaque acteur, individuellement, agit raisonnablement à l'intérieur d'un système qui produit collectivement de la dégradation.

Cette structure explique pourquoi les appels à la *« discipline »* ou à la *« concentration »* ne suffisent pas. Tant que les conditions structurelles qui rendent la sollicitation périphérique plus simple que son refus n'auront pas été modifiées, le problème ressurgira à chaque nouvelle pression sur l'organisation. La solution n'est pas comportementale. **Elle est architecturale.**

## VI. Redonner à l'expert le droit d'être spécialiste

Restaurer la concentration d'un expert dispersé n'est pas un acte de gestion ordinaire : c'est une décision stratégique qui engage le positionnement même de l'entreprise. Elle suppose plusieurs conditions que peu d'organisations réunissent spontanément.

La première est **la clarté du périmètre**. Chaque poste doit pouvoir être décrit en deux ou trois phrases qui distinguent ce qui en relève, ce qui en relève marginalement, et ce qui n'en relève pas. Cette formalisation est inconfortable parce qu'elle rend visibles les zones grises ; mais c'est précisément dans ces zones grises que la dispersion s'installe, en l'absence de critère pour la refuser.

La deuxième est **la légitimité du refus**. Dans une organisation où dire non à une mission périphérique est implicitement perçu comme un manque d'esprit d'équipe, aucun périmètre ne tiendra plus de quelques semaines. Le dirigeant doit non seulement autoriser le refus, mais en faire un comportement explicitement valorisé — y compris lorsque ce refus le contraint, lui-même, à chercher une autre solution.

La troisième est **la reconnaissance de l'expertise comme actif**. Tant que l'entreprise traite ses experts comme des ressources fongibles, interchangeables au gré des besoins, elle continuera à les disperser. Le changement de regard suppose que l'expertise soit identifiée, nommée, valorisée — dans les communications externes, dans les évaluations internes, dans les choix de recrutement. Une entreprise qui ne sait pas dire ce que font précisément ses experts ne sait pas, en réalité, ce qu'elle vend.

La quatrième est **l'acceptation d'un certain inconfort de court terme**. Restaurer un périmètre, c'est nécessairement refuser, déléguer ailleurs, parfois sous-traiter, parfois embaucher, parfois renoncer à une mission. Toutes ces décisions ont un coût visible immédiat — alors que les bénéfices, eux, ne deviennent mesurables qu'à un horizon de dix-huit à trente-six mois. Cette asymétrie temporelle est la raison pour laquelle la plupart des tentatives de re-concentration échouent : elles sont abandonnées au premier trimestre difficile, avant d'avoir produit leurs effets.

## VII. Ce que protéger ses experts veut dire

Une organisation qui protège ses experts n'est pas une organisation rigide. **Elle est une organisation lucide sur la nature de ce qu'elle vend.** Elle a compris que la polyvalence, en deçà d'un certain seuil de structuration, n'est pas une force mais un symptôme — celui d'une entreprise qui n'a pas encore les moyens, ou pas encore la volonté, de définir ce qu'elle est précisément en train de faire.

Protéger un expert, ce n'est pas le mettre sous cloche. C'est lui garantir qu'une part substantielle de son temps de travail sera consacrée à ce qu'il sait faire mieux que les autres ; que ses missions périphériques resteront périphériques en proportion comme en intensité ; qu'on lui demandera, à intervalles réguliers, de produire le travail de fond qui entretient sa compétence — veille, formation, expérimentation, écriture — et non seulement celui qui satisfait l'urgence du jour.

C'est, en somme, accepter que l'expertise n'est pas un don que l'on possède une fois pour toutes, mais *une pratique qui s'entretient ou qui s'éteint*. Une entreprise qui veut vendre de l'expertise doit, en interne, organiser les conditions de son entretien. Faute de quoi elle finira, sans s'en apercevoir, par vendre quelque chose d'autre — quelque chose de plus banal, de moins défendable, de moins rare — au même prix, jusqu'à ce que le marché finisse par lui faire remarquer la différence.

Un expert qui ne fait plus de l'expertise n'est pas, pour son entreprise, un avantage doublé : *c'est un coût caché qui mûrit*. Et l'on découvre, le jour où on le perd ou le jour où le client le compare, qu'on avait, pendant tout ce temps, payé pour une rareté que l'on s'était soi-même chargé de transformer en banalité.
"""


def main() -> None:
    print("Insertion de l'article 'Trop polyvalent pour être bon'...")

    slug = slugify(TITLE)

    author = User.objects.filter(is_superuser=True).first() or User.objects.first()

    category, _ = Category.objects.get_or_create(
        slug=CATEGORY_SLUG,
        defaults={"name": CATEGORY_NAME},
    )

    article, created = Article.objects.update_or_create(
        slug=slug,
        defaults={
            "title": TITLE,
            "subtitle": SUBTITLE,
            "category": category,
            "excerpt": EXCERPT,
            "body": BODY,
            "author": author,
            "is_published": True,
            "meta_description": META_DESCRIPTION,
        },
    )

    action = "créé" if created else "mis à jour"
    print(f"Article {action} : « {article.title} » (slug: {article.slug})")
    print(f"Catégorie : {category.name}")
    print(f"Auteur : {author}")
    print(f"URL : {article.get_absolute_url()}")


if __name__ == "__main__":
    main()
