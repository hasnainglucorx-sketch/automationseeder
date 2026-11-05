"""Extract public protobuf descriptors embedded in the deployed portal bundle."""
import base64
import json
from pathlib import Path
import re


def wire(data):
    i = 0
    def varint():
        nonlocal i
        n = shift = 0
        while True:
            b = data[i]
            i += 1
            n |= (b & 127) << shift
            if b < 128:
                return n
            shift += 7
    out = {}
    while i < len(data):
        tag = varint()
        number, kind = tag >> 3, tag & 7
        if kind == 0:
            value = varint()
        elif kind == 2:
            length = varint()
            value = data[i:i+length]
            i += length
        elif kind in (1, 5):
            length = 8 if kind == 1 else 4
            value = data[i:i+length]
            i += length
        else:
            raise ValueError('Unsupported wire type')
        out.setdefault(number, []).append(value)
    return out


def string(obj, number):
    return obj.get(number, [b''])[0].decode()


def enum(data):
    obj = wire(data)
    return {'name': string(obj, 1), 'values': {string(wire(v), 1): wire(v)[2][0] for v in obj.get(2, [])}}


def message(data):
    obj = wire(data)
    fields = []
    for raw in obj.get(2, []):
        f = wire(raw)
        fields.append({'name': string(f, 1), 'number': f[3][0], 'label': f.get(4, [1])[0],
                       'type': f[5][0], 'type_name': string(f, 6),
                       'oneof': f.get(9, [None])[0],
                       'behavior': wire(f.get(8, [b''])[0]).get(1052, [])})
    return {'name': string(obj, 1), 'fields': fields,
            'messages': [message(m) for m in obj.get(3, [])],
            'enums': [enum(e) for e in obj.get(4, [])]}


def extract(bundle):
    result = []
    for match in re.finditer(r'"([A-Za-z0-9+/]{80,}={0,2})"', bundle):
        try:
            data = base64.b64decode(match.group(1) + '===')
            if b'glucorx/modus/' not in data or b'proto3' not in data:
                continue
            obj = wire(data)
            result.append({'name': string(obj, 1), 'package': string(obj, 2),
                           'messages': [message(m) for m in obj.get(4, [])],
                           'enums': [enum(e) for e in obj.get(5, [])]})
        except (ValueError, IndexError, UnicodeDecodeError):
            continue
    return result


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    schema = extract((root / 'docs/portal.js').read_text(encoding='utf-8'))
    (root / 'schemas/deployed-messages.json').write_text(json.dumps(schema, indent=2), encoding='utf-8')
    print(f'Extracted {len(schema)} files')
