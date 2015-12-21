import string
import random
from . import app_settings

def transliterate(text):
    text = text.lower()
    mapping = {
        'а': 'a',
        'б': 'b',
        'в': 'v',
        'г': 'g',
        'д': 'd',
        'е': 'e',
        'ё': 'e',
        'ж': 'zh',
        'з': 'z',
        'и': 'i',
        'й': 'i',
        'к': 'k',
        'л': 'l',
        'м': 'm',
        'н': 'n',
        'о': 'o',
        'п': 'p',
        'р': 'r',
        'с': 's',
        'т': 't',
        'у': 'u',
        'ф': 'f',
        'х': 'kh',
        'ц': 'ts',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'shch',
        'ь': '',
        'ъ': '',
        'ы': 'y',
        'э': 'e',
        'ю': 'iu',
        'я': 'ia',
    }

    res = ''
    for s in text:
        if s in mapping:
            s = mapping[s]
        res += s
    return res

def trim_title(text):
    text = text.replace(' ', ' ') #Это не пробел, а какой-то гнилой символ
    text = text.encode('utf8').replace('и'.encode('utf8') + b'\xcc\x86', 'й'.encode('utf8')).decode('utf8')
    text = text.strip()
    return text

def full_trim(text):
    text = text.replace(':', '_')
    text = text.replace('»', '_')
    text = text.replace('№', '_')
    text = text.replace('«', '_')
    text = text.replace(' ', '_') #Это не пробел, а какой-то гнилой символ
    text = text.replace('…', '_')
    text = text.replace('-', '_')
    text = text.replace('–', '_')
    text = text.replace('—', '_')
    text = text.replace('@', '_')
    text = text.replace(',', '_')
    text = text.replace('-', '_')
    text = text.replace('.', '_')
    text = text.replace('!', '_')
    text = text.replace('?', '_')
    text = text.replace('   ', '_')
    text = text.replace('  ', '_')
    text = text.replace(' ', '_')
    text = text.replace('(', '_')
    text = text.replace(')', '_')
    text = text.replace('/', '_')
    text = text.replace('[', '_')
    text = text.replace(']', '_')
    text = text.replace('»', '_')
    text = text.replace('"', '_')
    text = text.replace('_____', '_')
    text = text.replace('____', '_')
    text = text.replace('____', '_')
    text = text.replace('___', '_')
    text = text.replace('___', '_')
    text = text.replace('___', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')
    text = text.replace('__', '_')

    if text[-1] == '_':
        text = text[:-1]
    if text[0] == '_':
        text = text[1:]

    text = text.strip()
    return text

def make_alias(text):
    return transliterate(full_trim(text))


def cut_text(text, length=100):
    res = text[:length]
    if not res == text:
        res += '...'
    return res

def check_bad_words(text):
    bad_words = app_settings.BAD_WORDS
    for bad_word in bad_words:
        if bad_word in text:
            return True
    return False

def get_digits_percent(text):
    total = len(text)
    digits_count = 0
    digits = map(str, range(10))

    for digit in digits:
        if digit in text:
            digits_count += text.count(digit)

    return (digits_count / total) * 100

def get_endlish_letters_percent(text):
    text = text.lower()

    total = len(text)
    engs_count = 0
    engs = string.ascii_lowercase

    for eng in engs:
        if eng in text:
            engs_count += text.count(eng)

    return (engs_count / total) * 100

def comment_body_ok(text):
    text = text.strip()
    text = text.replace("\r","")
    text = text.replace("\n","")
    text = text.replace(" ","")
    if get_digits_percent(text) > 60 or get_endlish_letters_percent(text) > 60 or check_bad_words(text):
        return False
    else:
        return True

def comment_author_ok(text):
    if check_bad_words(text):
        return False
    else:
        return True

def myround(x, base):
    return int(base * round(float(x)/base))

def to_int(val):
    try:
        res = int(val)
    except:
        res = 0
    return res

