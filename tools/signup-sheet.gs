/**
 * K12 BOSS website signups → Google Sheet.
 *
 * Setup (once, about 2 minutes):
 *  1. Open the "K12 BOSS — Website Signups" sheet in the K12 BOSS shared drive.
 *  2. Extensions → Apps Script. Replace everything in Code.gs with this file. Save.
 *  3. Deploy → New deployment → type "Web app".
 *       Execute as: Me
 *       Who has access: Anyone
 *     Click Deploy, approve the permissions prompt, and copy the Web app URL
 *     (it ends in /exec). That URL goes into the site build as NOTIFY_ENDPOINT.
 *
 * The site posts {email, list, name, role, school, page}. One row per email per list;
 * repeats are ignored. List is "Launch" (episode 1 alert) or "Community" (invite).
 */
var HEADERS = ['Timestamp', 'Email', 'List', 'Name', 'Role', 'School or district', 'Page'];

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var data = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var email = String(data.email || '').trim().toLowerCase();
    if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return json({ ok: false, error: 'invalid_email' });
    }
    var list = clean(data.list, 40) || 'Launch';
    var page = clean(data.page, 200);
    var name = clean(data.name, 120);
    var role = clean(data.role, 60);
    var school = clean(data.school, 160);

    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    var last = sheet.getLastRow();
    if (last > 1) {
      var rows = sheet.getRange(2, 2, last - 1, 2).getValues();
      for (var i = 0; i < rows.length; i++) {
        if (String(rows[i][0]).replace(/^'/, '') === email && rows[i][1] === list) {
          return json({ ok: true, duplicate: true });
        }
      }
    }
    sheet.appendRow([new Date(), safe(email), list, safe(name), safe(role), safe(school), safe(page)]);
    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: 'server_error' });
  } finally {
    lock.releaseLock();
  }
}

function clean(v, max) {
  return String(v || '').replace(/[\r\n\t]/g, ' ').trim().slice(0, max);
}

// Stop values that start with = + - @ from being read as spreadsheet formulas.
function safe(v) {
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
