"""Response comparison and pagination independent of authentication and transport."""


def camel_case(name: str) -> str:
    """Map a protobuf snake_case field to its JSON response spelling."""
    first, *rest = name.split('_')
    return first + ''.join(part.title() for part in rest)


def matches_payload(expected, actual):
    """Compare planned fields, allowing additional server response fields."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(matches_payload(value, actual.get(camel_case(key)))
                   for key, value in expected.items())
    return expected == actual


def collect_pages(request, method, body, key):
    """Collect a unary RPC's pages without modifying the caller's request.

    request(method, body) supplies authentication on each call. Repeated cursors
    are rejected to prevent an endless loop or silently duplicated results.
    """
    result, seen = [], set()
    body = dict(body, page_size=1000)
    while True:
        response = request(method, body)
        result.extend(response.get(key, []))
        token = response.get('nextPageToken')
        if not token:
            return result
        if token in seen:
            raise RuntimeError('Repeated pagination cursor')
        seen.add(token)
        body['page_token'] = token
