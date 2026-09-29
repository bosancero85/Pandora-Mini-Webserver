// Prüft die Betriebssystem-Erkennung aus index.html. Start: node tests/detect_os.test.js
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const vm = require('vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const m = html.match(/\/\/ <download-logic>([\s\S]*?)\/\/ <\/download-logic>/);
assert(m, 'Marker <download-logic> nicht gefunden');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(m[1] + '\nthis.detect = mwDetectPlatform; this.key = mwAssetKey; this.url = mwDownloadUrl; this.files = MW_FILES;', ctx);

const UA = {
  win: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
  winArm: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36',
  macSafari: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
  linuxFf: 'Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0',
  linuxArm: 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36',
  linuxArm32: 'Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
  android: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36',
  iphone: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1',
  ipadDesktop: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15',
  chromeos: 'Mozilla/5.0 (X11; CrOS x86_64 15662.76.0) AppleWebKit/537.36 Chrome/130.0 Safari/537.36',
};

const cases = [
  ['Windows Chrome', { userAgent: UA.win, platform: 'Win32' }, {}, 'windows', 'windows-x64'],
  ['Windows mit Client-Hints', { userAgent: UA.winArm, userAgentData: { platform: 'Windows' } }, { architecture: 'arm' }, 'windows', 'windows-x64'],
  ['Mac Safari ohne Hinweis -> Apple Silicon', { userAgent: UA.macSafari, platform: 'MacIntel', maxTouchPoints: 0 }, {}, 'macos', 'macos-arm64'],
  ['Mac Chrome Hinweis arm', { userAgent: UA.macSafari, userAgentData: { platform: 'macOS' } }, { architecture: 'arm' }, 'macos', 'macos-arm64'],
  ['Mac Chrome Hinweis x86 -> Intel', { userAgent: UA.macSafari, userAgentData: { platform: 'macOS' } }, { architecture: 'x86' }, 'macos', 'macos-x86_64'],
  ['Linux Firefox x86_64', { userAgent: UA.linuxFf, platform: 'Linux x86_64' }, {}, 'linux', 'linux-x86_64'],
  ['Linux aarch64 (Raspberry Pi)', { userAgent: UA.linuxArm, platform: 'Linux aarch64' }, {}, 'linux', 'linux-arm64'],
  ['Linux 32-Bit-ARM -> kein Paket', { userAgent: UA.linuxArm32, platform: 'Linux armv7l' }, {}, 'linux', null],
  ['Linux ohne Architektur -> x86_64', { userAgent: 'Mozilla/5.0 (X11; Linux) Gecko', platform: 'Linux' }, {}, 'linux', 'linux-x86_64'],
  ['Android (UA enthält Linux)', { userAgent: UA.android, platform: 'Linux armv8l', maxTouchPoints: 5 }, {}, 'android', null],
  ['iPhone (UA enthält Mac OS X)', { userAgent: UA.iphone, platform: 'iPhone', maxTouchPoints: 5 }, {}, 'ios', null],
  ['iPad im Desktop-Modus', { userAgent: UA.ipadDesktop, platform: 'MacIntel', maxTouchPoints: 5 }, {}, 'ios', null],
  ['ChromeOS', { userAgent: UA.chromeos, platform: 'Linux x86_64' }, {}, 'unknown', null],
  ['leeres Objekt', {}, {}, 'unknown', null],
  ['undefined', undefined, undefined, 'unknown', null],
];

let failed = 0;
for (const [name, nav, hint, os, key] of cases) {
  try {
    const det = ctx.detect(nav, hint);
    assert.strictEqual(det.os, os, 'OS');
    assert.strictEqual(ctx.key(det.os, det.arch), key, 'Paket');
    console.log('ok   ' + name);
  } catch (e) {
    failed++;
    console.log('FAIL ' + name + ': ' + e.message);
  }
}

// Download-URL stabil und ohne Versionsnummer
assert.ok(/^https:\/\/github\.com\/[^/]+\/[^/]+\/releases\/latest\/download\/MiniWebserver-Windows-x64\.exe$/.test(ctx.url(ctx.files['windows-x64'])));
console.log('ok   Download-URL');
if (failed) { console.log(failed + ' Test(s) fehlgeschlagen'); process.exit(1); }
console.log('Alle ' + (cases.length + 1) + ' Prüfungen bestanden');
