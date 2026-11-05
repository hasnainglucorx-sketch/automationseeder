from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import csv
import html
import math
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tmp' / 'qr-code-deps'))
import qrcode
import zxingcpp
from PIL import Image

now_utc = datetime.now(timezone.utc)
pkt = ZoneInfo('Asia/Karachi')
D = now_utc.astimezone(pkt).date()
out = ROOT / f'qr_codes_{D.isoformat()}'
out.mkdir(exist_ok=True)
T = now_utc + timedelta(days=15)
X = (T + timedelta(hours=14)).replace(hour=0, minute=0, second=0, microsecond=0)
E = X.date()
start = X - timedelta(hours=14, days=15)
end = X + timedelta(hours=11) - timedelta(days=15)
lines = [f'PKT date D: {D}', f'Current UTC time: {now_utc.isoformat()}',
         f'T: {T.isoformat()}', f'X: {X.isoformat()}', f'E: {E}',
         f'Scan window UTC: [{start.isoformat()}, {end.isoformat()})',
         f'Scan window PKT: [{start.astimezone(pkt).isoformat()}, {end.astimezone(pkt).isoformat()})',
         'Start inclusive; end exclusive.',
         'Inside this window: Kiritimati (UTC+14) must reject; Pago Pago (UTC-11) must accept.']
if not start <= now_utc < end:
    lines.append('WARNING: Current time is OUTSIDE the valid scanning window!')
else:
    lines.append('Current time is inside the valid scanning window.')

rows = [
    ['SENSOR-VALID-01', '01095060001343521730123121SN0001234', '2030-12-31', 'SN0001234', 'Fixed expiry'],
    ['BARCODE-WRONGTYPE-01', '01095060001343691730123121TX0001234', '2030-12-31', 'TX0001234', 'User-supplied fixed wrong-type test payload'],
    ['SENSOR-RECALLED-01', '01095060001343521730123121SN0000999', '2030-12-31', 'SN0000999', 'User-supplied fixed recall test payload; recall status is checked by the app/backend'],
    ['SENSOR-EXPIRED-01', '01095060001343521722123121SN0009999', '2022-12-31', 'SN0009999', 'Fixed expiry'],
]
for days, serial in [(15, 'SN0001515'), (16, 'SN0001516')]:
    expiry = D + timedelta(days=days)
    rows.append([f'SENSOR-EXPIRY-{days}D-01', '0109506000134352' + '17' + expiry.strftime('%y%m%d') + '21' + serial,
                 expiry.isoformat(), serial, f'D + {days} days; D = {D} PKT'])
rows.append(['SENSOR-EXPIRY-TZ-01', '0109506000134352' + '17' + E.strftime('%y%m%d') + '21SN0001600',
             E.isoformat(), 'SN0001600', f'UTC+14 reject / UTC-11 accept only within [{start.isoformat()}, {end.isoformat()})'])

for ident, payload, expiry, serial, note in rows:
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4, box_size=1)
    code.add_data(payload)
    code.make(fit=True)
    code.box_size = math.ceil(1000 / (code.modules_count + 8))
    path = out / f'{ident}.png'
    code.make_image(fill_color='black', back_color='white').save(path)
    with Image.open(path) as image:
        assert min(image.size) >= 1000, (ident, image.size)
        decoded = zxingcpp.read_barcodes(image)
        assert len(decoded) == 1, f'{ident}: expected exactly one decoded barcode'
        assert decoded[0].text == payload, f'{ident}: decoded text does not match'
    lines.append(f'PASS: {ident}: decoded text matches exactly')

headers = ['ID', 'text', 'expiry date', 'serial', 'note']
with (out / 'codes.csv').open('w', encoding='utf-8', newline='') as handle:
    writer = csv.writer(handle)
    writer.writerow(headers)
    writer.writerows(rows)
widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(5)]
lines.append(' | '.join(value.ljust(widths[i]) for i, value in enumerate(headers)))
lines.append('-+-'.join('-' * width for width in widths))
lines.extend(' | '.join(value.ljust(widths[i]) for i, value in enumerate(row)) for row in rows)
report = '\n'.join(lines)
(out / 'verification.txt').write_text(report, encoding='utf-8')
cards = ''.join(f'<figure><img src="{ident}.png" alt="{ident}"><figcaption><strong>{ident}</strong><br>Expiry: {expiry}<br>Serial: {serial}</figcaption></figure>' for ident, payload, expiry, serial, note in rows)
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Phone-app test barcodes</title>
<style>@page{size:A4;margin:10mm}body{font-family:Arial,sans-serif;margin:0;color:#000;background:#fff}h1{font-size:18px;margin:0 0 5px}p{font-size:11px;margin:4px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:4mm}figure{margin:0;text-align:center;break-inside:avoid}img{width:45mm;height:45mm;image-rendering:pixelated}figcaption{font-size:11px;line-height:1.4}footer{font-size:10px;margin-top:4mm}</style>
'''+f'<h1>Phone-app test barcodes</h1><p>PKT date D: {D}</p><p>TZ scan window (PKT): {start.astimezone(pkt).strftime("%d %b %Y %H:%M")} inclusive to {end.astimezone(pkt).strftime("%d %b %Y %H:%M")} exclusive.</p><div class="grid">{cards}</div><footer>Timezone test: UTC+14 reject; UTC-11 accept, only inside the stated window. All seven PNGs decoded and matched exactly using zxing-cpp.</footer></html>'
(out / 'qr_codes.html').write_text(page, encoding='utf-8')
print(report)
