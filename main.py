import feedparser
import requests
import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '432302545')
ROME = ZoneInfo('Europe/Rome')

KEYWORDS_IT = ['amore','relazione','relazioni','coppia','coppie','sesso','tradimento','rottura','gelosia','solitudine','autostima','dipendenza affettiva','ex ','flirt','seduzione','attrazione','innamorarsi','lasciare','lasciato','cuore spezzato','narcisismo','manipolazione','tossico','fidanzato','fidanzata','matrimonio','divorzio','single','appuntamento']
KEYWORDS_EN = ['love','relationship','relationships','dating','sex','breakup','marriage','couple','couples','cheating','infidelity','jealousy','loneliness','self-esteem','attachment','toxic','narcissist','narcissism','manipulation','heartbreak','flirting','seduction','attraction','divorce','affair','emotional abuse','red flags','ghosting','situationship','trauma bond']
ALL_KEYWORDS = KEYWORDS_IT + KEYWORDS_EN

# ============================================================
# COMPETITOR INSTAGRAM — aggiungi qui gli username dei tuoi competitor
# Esempio: 'nomeutente' (senza @)
# ============================================================
COMPETITOR_ACCOUNTS = [
    # Competitor gruppo 1 (6)
    'federico picchianti',
    'maryjbaccaglini',
    'federicoseverino',
    'lucaromito',
    'monica ricci',
    'benedetta gherardini',
    # Competitor gruppo 2 (11)
    'psicologiamanipolativa',
    'laexincazzata',
    'serenis.it',
    'dr.enrico.gamba',
    'drfantechi',
    'danieledibenedetti',
    'maurizioromano83',
    'rob_wildside',
    'dr.matteosinattipsicologo',
    'alessiofiorucci',
    'psicologo_francesco_boz',
]

SOURCES_IT = [
    {'name': 'iO Donna', 'url': 'https://www.iodonna.it/amore/feed/'},
    {'name': 'Corriere della Sera', 'url': 'https://www.corriere.it/rss/lifestyle.xml'},
    {'name': 'Repubblica', 'url': 'https://www.repubblica.it/rss/lifestyle/rss2.0.xml'},
    {'name': 'Grazia', 'url': 'https://www.grazia.it/feed'},
    {'name': 'Vanity Fair Italia', 'url': 'https://www.vanityfair.it/feed'},
    {'name': 'Donna Moderna', 'url': 'https://www.donnamoderna.com/feed'},
    {'name': 'Dilei', 'url': 'https://dilei.it/amore/feed/'},
    {'name': 'Cosmopolitan Italia', 'url': 'https://www.cosmopolitan.com/it/amore-sesso/feed/'},
]

SOURCES_EN = [
    {'name': 'Reddit r/relationships', 'url': 'https://www.reddit.com/r/relationships/.rss?limit=25'},
    {'name': 'Reddit r/dating_advice', 'url': 'https://www.reddit.com/r/dating_advice/.rss?limit=25'},
    {'name': 'Reddit r/love', 'url': 'https://www.reddit.com/r/love/.rss?limit=25'},
    {'name': 'Reddit r/relationship_advice', 'url': 'https://www.reddit.com/r/relationship_advice/.rss?limit=25'},
    {'name': 'Psychology Today', 'url': 'https://www.psychologytoday.com/intl/blog/feed'},
    {'name': 'Verywell Mind', 'url': 'https://www.verywellmind.com/feed'},
    {'name': 'MindBodyGreen', 'url': 'https://www.mindbodygreen.com/rss.xml'},
    {'name': 'Gottman Institute', 'url': 'https://www.gottman.com/blog/feed/'},
    {'name': 'Psych Central', 'url': 'https://psychcentral.com/feed/'},
    {'name': 'Bustle', 'url': 'https://www.bustle.com/relationships.rss'},
    {'name': 'Refinery29', 'url': 'https://www.refinery29.com/en-us/love/rss.xml'},
    {'name': 'HuffPost', 'url': 'https://www.huffpost.com/section/relationships/feed'},
    {'name': 'Cosmopolitan', 'url': 'https://www.cosmopolitan.com/sex-love/rss/'},
    {'name': "Women's Health", 'url': 'https://www.womenshealthmag.com/uk/relationships/feed/'},
    {'name': 'The Date Mix', 'url': 'https://www.zoosk.com/date-mix/feed/'},
    {'name': 'Red Magazine', 'url': 'https://www.redonline.co.uk/relationships/feed/'},
]

ALL_SOURCES = SOURCES_IT + SOURCES_EN


def get_yesterday():
    now = datetime.now(ROME)
    yesterday = now - timedelta(days=1)
    return yesterday.date()


def parse_date(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            import calendar
            ts = calendar.timegm(entry.published_parsed)
            return datetime.fromtimestamp(ts, tz=ROME).date()
    except:
        pass
    return None


def matches_keywords(text):
    text_lower = text.lower()
    for kw in ALL_KEYWORDS:
        pattern = r'\b' + re.escape(kw.strip()) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False


def translate_title(title):
    try:
        from googletrans import Translator
        t = Translator()
        result = t.translate(title, dest='it')
        return result.text
    except:
        return title


def scrape_source(source):
    articles = []
    yesterday = get_yesterday()
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; ViralLoveCoachBot/1.0)'}
        feed = feedparser.parse(source['url'], request_headers=headers)
        for entry in feed.entries[:20]:
            entry_date = parse_date(entry)
            if entry_date != yesterday:
                continue
            title = entry.get('title', '')
            summary = entry.get('summary', entry.get('description', ''))
            link = entry.get('link', '')
            text = title + ' ' + summary
            if matches_keywords(text):
                translated = translate_title(title)
                articles.append({'title': translated, 'link': link})
    except Exception as e:
        print(f'Errore {source["name"]}: {e}')
    return articles


def scrape_instagram_competitor(username):
    """Recupera i post Instagram di ieri da un profilo pubblico."""
    posts_found = []
    yesterday = get_yesterday()
    try:
        import instaloader
        L = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True
        )
        profile = instaloader.Profile.from_username(L.context, username)
        for post in profile.get_posts():
            post_date = post.date_utc.astimezone(ROME).date()
            # Ferma se arriviamo a post troppo vecchi
            if post_date < yesterday:
                break
            if post_date == yesterday:
                caption = post.caption or ''
                first_line = caption.split('\n')[0][:120].strip()
                if not first_line:
                    first_line = '[nessuna didascalia]'
                post_url = f'https://www.instagram.com/p/{post.shortcode}/'
                posts_found.append({
                    'title': first_line,
                    'link': post_url,
                    'likes': post.likes,
                    'type': 'VIDEO' if post.is_video else 'POST'
                })
    except Exception as e:
        print(f'Errore Instagram @{username}: {e}')
        return None  # None = errore, lista vuota = nessun post ieri
    return posts_found


def build_competitors_section():
    """Costruisce la sezione competitor Instagram per il report."""
    if not COMPETITOR_ACCOUNTS or COMPETITOR_ACCOUNTS[0] == 'competitor1_username':
        return '', 0  # Placeholder non ancora configurato
    lines = []
    total_posts = 0
    for username in COMPETITOR_ACCOUNTS:
        result = scrape_instagram_competitor(username)
        if result is None:
            lines.append(f'\U0001f4f7 @{username} \u2192 \u26a0\ufe0f errore nel recupero')
        elif len(result) == 0:
            lines.append(f'\U0001f4f7 @{username} \u2192 \u2716 nessun post ieri')
        else:
            count = len(result)
            total_posts += count
            lines.append(f'\U0001f4f7 @{username} \u2192 {count} post ieri')
            for i, p in enumerate(result, 1):
                label = f'[{p["type"]}]' if p['type'] == 'VIDEO' else ''
                lines.append(f'  {i}. {label} "{p["title"]}" ({p["likes"]} \u2764\ufe0f) \u2192 {p["link"]}')
    return '\n'.join(lines), total_posts


def send_telegram(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f'Errore Telegram: {e}')
        return False


def build_section(sources):
    lines = []
    total = 0
    for source in sources:
        articles = scrape_source(source)
        if not articles:
            lines.append(f'\U0001f4f0 {source["name"]} \u2192 \u2716 nessun articolo rilevante')
        else:
            count = len(articles)
            total += count
            lines.append(f'\U0001f4f0 {source["name"]} \u2192 {count} articol{"o" if count==1 else "i"}')
            for i, a in enumerate(articles[:5], 1):
                lines.append(f'  {i}. "{a["title"]}" \u2192 {a["link"]}')
    return '\n'.join(lines), total


def run():
    yesterday = get_yesterday()
    date_str = yesterday.strftime('%-d %B %Y')\
        .replace('January','Gennaio').replace('February','Febbraio')\
        .replace('March','Marzo').replace('April','Aprile')\
        .replace('May','Maggio').replace('June','Giugno')\
        .replace('July','Luglio').replace('August','Agosto')\
        .replace('September','Settembre').replace('October','Ottobre')\
        .replace('November','Novembre').replace('December','Dicembre')

    print(f'Avvio briefing per {date_str}...')

    it_text, it_total = build_section(SOURCES_IT)
    en_text, en_total = build_section(SOURCES_EN)
    comp_text, comp_total = build_competitors_section()
    grand_total = it_total + en_total

    # Messaggio 1: fonti italiane
    msg1 = (
        f'\U0001f4cb BRIEFING LOVE COACH \u2014 {date_str} (1/3)\n'
        f'\u2501' * 22 + '\n'
        f'\U0001f1ee\U0001f1f9 FONTI ITALIANE\n'
        f'\u2501' * 22 + '\n'
        f'{it_text}'
    )

    # Messaggio 2: fonti internazionali
    msg2 = (
        f'\U0001f4cb BRIEFING LOVE COACH \u2014 {date_str} (2/3)\n'
        f'\u2501' * 22 + '\n'
        f'\U0001f30d FONTI INTERNAZIONALI\n'
        f'\u2501' * 22 + '\n'
        f'{en_text}\n'
        f'\u2501' * 22 + '\n'
        f'\u2705 Articoli rilevanti oggi: {grand_total}'
    )

    # Messaggio 3: competitor Instagram
    if comp_text:
        msg3 = (
            f'\U0001f4cb BRIEFING LOVE COACH \u2014 {date_str} (3/3)\n'
            f'\u2501' * 22 + '\n'
            f'\U0001f575\ufe0f COMPETITOR INSTAGRAM\n'
            f'\u2501' * 22 + '\n'
            f'{comp_text}\n'
            f'\u2501' * 22 + '\n'
            f'\U0001f4f7 Post competitor ieri: {comp_total}'
        )
    else:
        msg3 = None

    for msg in ([msg1, msg2] + ([msg3] if msg3 else [])):
        chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
        for chunk in chunks:
            send_telegram(chunk)

    print(f'Report inviato! Articoli: {grand_total}, Post competitor: {comp_total}')


if __name__ == '__main__':
    run()
