"""kanji_extra.tsv: readings of the kanji that are not 常用漢字, for the card of one kanji typed alone (乎, 鷗, 淵).

    python -I tools/build_kanji_extra.py path/to/kanjidic2.xml.gz app/src/main/assets/kanji_extra.tsv

The source is KANJIDIC2 (EDRDG, https://www.edrdg.org/wiki/index.php/KANJIDIC_Project, CC BY-SA 4.0): the readings of
each kanji, nothing of its English meanings. It takes the kanji of JIS X 0208 (levels 1 and 2) and the 人名用漢字 (grades
9 and 10 there) and the commoner of the rest (those with a frequency), that are not in the 常用漢字表 (assets/joyo_readings.tsv), with 音読み (hiragana) and 訓読み (a dot before
the okurigana), most usual first as KANJIDIC2 gives them. Output: kanji TAB 音読み (comma-separated) TAB 訓読み TAB kind,
J for a 人名用漢字 and H for the others (表外漢字).
"""
import gzip
import os
import sys
import xml.etree.ElementTree as ET

MOST_ON, MOST_KUN = 6, 8
# What a check of 150 of them against what is known of Japanese found wrong in KANJIDIC2's data.
MOVE_TO_ON = {'喙': ['がい'], '牌': ['ぱい']}
# Readings KANJIDIC2 has wrong or mixed with another kanji's, found by the reviewers of the kanji cards: kanji -> (音読み, 訓読み).
READING_FIX = {
    '綾': (['りょう'], ['あや']), '碓': (['たい'], ['うす']), '竣': (['しゅん'], ['おわ.る']),
    '姜': (['きょう', 'こう'], ['はじかみ']), '崔': (['さい', 'すい'], []), '汐': (['せき'], ['しお', 'うしお']),
    '篠': (['しょう'], ['しの', 'ささ', 'すず']), '莫': (['ばく', 'ぼ', 'まく', 'も'], ['くれ', 'なか.れ', 'なし']),
    '諄': (['じゅん', 'しゅん'], ['ひちくど.い', 'くど.い', 'くどくど', 'ねんご.ろ']), '諏': (['しゅ', 'す'], ['はか.る']),
    '轍': (['てつ'], ['わだち']), '陀': (['だ', 'た'], []),
}
KUN_FIX = {('坡', 'つつ.み'): 'つつみ', ('慵', 'ものうい'): 'ものう.い', ('糢', 'のっとる'): 'のっと.る'}


def hiragana(s):
    return ''.join(chr(ord(c) - 0x60) if '\u30a1' <= c <= '\u30f6' else c for c in s)


def joyo(path):
    out = set()
    for line in open(path, encoding='utf-8'):
        if line.startswith('#') or line.startswith('=') or not line.strip():
            continue
        head = line.split('\t')[0]
        if len(head) == 1:
            out.add(head)
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, out = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(out))
    known = joyo(os.path.join(here, 'joyo_readings.tsv'))
    root = ET.fromstring(gzip.open(source, 'rb').read())
    rows = []
    for ch in root.findall('character'):
        literal = ch.findtext('literal')
        if literal in known:
            continue
        # The compatibility ideographs (U+F900 to U+FAFF) are old letter forms KANJIDIC2 lists apart: nobody types them.
        if '豈' <= literal <= '﫿':
            continue
        misc = ch.find('misc')
        grade = misc.findtext('grade') if misc is not None else None
        jis = any(c.get('cp_type') == 'jis208' for c in ch.findall('codepoint/cp_value'))
        if not jis and grade not in ('9', '10'):
            continue
        # The 人名用漢字, and of the others only those KANJIDIC2 has a newspaper frequency for: a check of 150 of all of
        # them found one in twenty with a doubtful reading, nearly all among the rarest.
        if grade not in ('9', '10') and not misc.findtext('freq'):
            continue
        on, kun = [], []
        for r in ch.findall('reading_meaning/rmgroup/reading'):
            if r.get('r_type') == 'ja_on':
                x = hiragana(r.text)
                if x not in on:
                    on.append(x)
            elif r.get('r_type') == 'ja_kun':
                x = r.text.replace('-', '')
                if x and x not in kun:
                    kun.append(x)
        # KANJIDIC2's few slips found in a check of a sample (an 音読み among the 訓読み, a missing dot, a noun with one).
        for x in MOVE_TO_ON.get(literal, []):
            if x in kun:
                kun.remove(x)
                on.append(x)
        kun = [KUN_FIX.get((literal, x), x) for x in kun]
        if literal in READING_FIX:
            on, kun = list(READING_FIX[literal][0]), list(READING_FIX[literal][1])
        if not on and not kun:
            continue
        rows.append((literal, ','.join(on[:MOST_ON]), ','.join(kun[:MOST_KUN]), 'J' if grade in ('9', '10') else 'H'))
    rows.sort(key=lambda r: ord(r[0]))
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# kanji_extra: readings of kanji that are not 常用漢字 (人名用漢字 J, 表外漢字 H), from KANJIDIC2 (EDRDG, CC BY-SA 4.0). '
                'kanji TAB 音読み TAB 訓読み (a dot before the okurigana) TAB J or H; tools/build_kanji_extra.py\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    print(len(rows), 'kanji', sum(r[3] == 'J' for r in rows), 'jinmei')


main()
