"""Post-deployment HTTPS/WS verification; credentials stay in process memory."""
import http.cookiejar
import json
import os
import urllib.request
from urllib.error import HTTPError
from websockets.sync.client import connect
from websockets.exceptions import InvalidStatus, ConnectionClosed

base = 'https://davefrassoni.com/cyberar/'
jar = http.cookiejar.CookieJar()
http = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def call(path, data=None, csrf=None):
    headers = {'User-Agent': 'CYBERAR-Smoke/1.0', 'Content-Type': 'application/json', 'Origin': 'https://davefrassoni.com'}
    if csrf: headers['X-CSRFToken'] = csrf
    req = urllib.request.Request(base+'api/'+path+'/', data=None if data is None else json.dumps(data).encode(), headers=headers)
    with http.open(req, timeout=15) as response: return json.load(response)

try:
    call('state')
    raise AssertionError('Unauthenticated state leaked')
except HTTPError as error: assert error.code == 401
csrf = call('session')['csrf']
csrf = call('login', {'username':os.environ['CYBERAR_USER'], 'password':os.environ['CYBERAR_PASSWORD']}, csrf)['csrf']
initial = call('state')
assert initial['elapsed'] == 0
cookies = '; '.join(f'{cookie.name}={cookie.value}' for cookie in jar)
url = 'wss://davefrassoni.com/cyberar/ws/mission/'
try:
    with connect(url, origin='https://attacker.invalid', additional_headers={'Cookie':cookies}):
        raise AssertionError('Foreign websocket origin accepted')
except InvalidStatus as error: assert error.response.status_code == 403
with connect(url, origin='https://davefrassoni.com', additional_headers={'Cookie':cookies}) as socket:
    frame = json.loads(socket.recv(timeout=5))
    assert frame['mission_id'] == initial['mission_id']
    call('control', {'action':'automatic_demo'}, csrf)
    call('control', {'action':'speed', 'value':4}, csrf)
    for _ in range(8):
        frame = json.loads(socket.recv(timeout=5))
        if frame['elapsed'] >= 4: break
    assert frame['elapsed'] >= 4 and frame['telemetry']['x'] != initial['telemetry']['x']
    call('control', {'action':'pause'}, csrf)
    manual = call('control', {'action':'interference', 'value':85}, csrf)
    assert manual['channels'][0]['packet_loss'] > 50
    ground = call('control', {'action':'can_start'}, csrf)
    assert ground['ugv']['level'] == 15 and ground['ugv']['manual']
    ground = call('control', {'action':'can_increase'}, csrf)
    assert ground['ugv']['level'] == 45
    ground = call('control', {'action':'can_restore'}, csrf)
    assert ground['ugv']['level'] == 0 and ground['interference'] == 85
    reset = call('control', {'action':'reset'}, csrf)
    for key in ['revision']: initial.pop(key); reset.pop(key)
    assert reset == initial
    call('logout', {}, csrf)
    for _ in range(5):
        try: socket.recv(timeout=3)
        except ConnectionClosed as error:
            assert error.code == 4401
            break
    else: raise AssertionError('WebSocket stayed active after logout')
assert not call('session')['authenticated']
print('PASS: HTTPS auth, CSRF, mission, WSS stream, origin rejection, server clock, controls, reset, logout')
