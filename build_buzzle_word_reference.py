"""Render the exact two-letter subset of the released BUZZLE dictionary."""
import hashlib
import json
import re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / 'assets/reference/buzzle-two-letter-words.json'
OUT = ROOT / 'output/pdf/BUZZLE_Two_Letter_Words.pdf'


def snapshot_dictionary(source):
    meta = json.loads(source.with_suffix('.meta.json').read_text())
    data = source.read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(data).hexdigest() == meta['sha256']
    words = sorted({word.upper() for word in data.decode().splitlines()
                    if re.fullmatch('[a-z]{2}', word)})
    REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    REFERENCE.write_text(json.dumps({
        'source_url': 'https://aresfirst.org/data/buzzle-words.txt',
        'source_commit': '547a638099d35b6c596d290113cc159724fff163',
        'verified_from': 'Released website source; dictionary matches its recorded SHA-256',
        'date': '2026-09-06', 'dictionary': meta, 'words': words,
    }, indent=2)+'\n', encoding='utf-8')


def build():
    record = json.loads(REFERENCE.read_text())
    words = record['words']
    assert words == sorted(set(words))
    assert all(re.fullmatch('[A-Z]{2}', w) for w in words)
    assert len(words) <= 136, 'Increase layout capacity before adding more words.'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(612,792))
    c.setTitle('BUZZLE - Two-Letter Words')
    c.setAuthor('ARES FTC 23247')
    c.setFillColor(HexColor('#F3D928'))
    c.rect(0,775,612,17,fill=1,stroke=0)
    c.setFillColor(HexColor('#161819'))
    c.setFont('Helvetica-Bold',30)
    c.drawString(36,735,'BUZZLE')
    c.setFont('Helvetica-Bold',12)
    c.drawRightString(576,741,f'{len(words)} WORDS')
    c.setFont('Helvetica-Bold',19)
    c.drawString(36,700,'TWO-LETTER WORDS')
    c.setFont('Helvetica',10)
    c.drawString(36,678,'An alphabetical reference for the ARES BUZZLE word list.')
    c.drawString(36,662,'Read across each row. Other dictionaries may accept a different set.')
    width=540/8
    for row in range((len(words)+7)//8):
        top=636-row*31
        if row%2 == 0:
            c.setFillColor(HexColor('#F2F3F3'))
            c.rect(36,top-31,540,31,fill=1,stroke=0)
        for col,word in enumerate(words[row*8:(row+1)*8]):
            c.setFillColor(HexColor('#161819'))
            c.setFont('Helvetica-Bold',17)
            c.drawCentredString(36+(col+.5)*width,top-22,word)
    c.setFillColor(HexColor('#161819'))
    c.setFont('Helvetica',10)
    c.drawString(36,111,'Every crossing word must still be valid, and normal placement rules apply.')
    c.setFillColor(HexColor('#08679B'))
    c.setFont('Helvetica-Bold',11)
    c.drawString(36,87,'Word checker, dictionary and current list:')
    c.drawString(36,70,'aresfirst.org/buzzle/word-tools')
    c.linkURL('https://aresfirst.org/buzzle/word-tools',(36,66,400,83),relative=0)
    c.setStrokeColor(HexColor('#C9CDD0'))
    c.setLineWidth(.5)
    c.line(36,55,576,55)
    c.setFillColor(HexColor('#161819'))
    c.setFont('Helvetica',8)
    c.drawString(36,39,'ARES FTC 23247 | BUZZLE dictionary snapshot: September 6, 2026')
    c.drawRightString(576,39,'1 / 1')
    c.setFont('Helvetica',7)
    c.drawString(36,24,'Source: an-array-of-english-words 2.0.0 (MIT), as filtered and shipped by ARES BUZZLE.')
    c.save()
    pdf = PdfReader(OUT)
    assert len(pdf.pages) == 1
    extracted = re.findall(r'\b[A-Z]{2}\b', pdf.pages[0].extract_text())
    assert extracted == words, 'PDF must contain every listed word exactly once in alphabetical order.'
    print(f'PASS: {len(words)} exact dictionary entries, one page, no omissions or duplicates.')


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--dictionary',type=Path)
    args=parser.parse_args()
    if args.dictionary:
        snapshot_dictionary(args.dictionary)
    build()
