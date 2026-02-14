/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * gas-hoggle-api.gs — Hoggle API Endpoint for n8n Roster Sync
 * ═══════════════════════════════════════════════════════════════════════════════
 *
 * ADD THIS FILE to your Multimedia Heroes Google Apps Script project.
 *
 * SETUP STEPS:
 * 1. Open your Multimedia Heroes spreadsheet
 * 2. Go to Extensions → Apps Script
 * 3. Click + next to Files → Script → name it "25_Module_HoggleAPI"
 * 4. Paste this entire file
 * 5. Go to Project Settings → Script Properties → Add:
 *    Property: HOGGLE_API_SECRET
 *    Value: (make up a random string, like "hoggle-sync-abc123")
 * 6. Deploy → New Deployment → Web App
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 7. Copy the deployment URL into your n8n roster sync workflow
 *
 * IMPORTANT: After adding this file, you must create a NEW deployment
 * (or update existing) for the doPost handler to be active.
 *
 * @version 1.0.0
 * ═══════════════════════════════════════════════════════════════════════════════
 */

/**
 * HTTP POST handler for Hoggle API calls from n8n
 *
 * Supported actions:
 * - hoggle-roster: Returns anonymized student roster for local caching
 * - hoggle-ping: Health check
 *
 * Request format:
 * {
 *   "action": "hoggle-roster",
 *   "secret": "your-shared-secret"
 * }
 */
function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var action = body.action;

    // Validate shared secret for all actions
    var expectedSecret = PropertiesService.getScriptProperties().getProperty('HOGGLE_API_SECRET');
    if (!expectedSecret || body.secret !== expectedSecret) {
      return jsonResponse({ success: false, error: 'Unauthorized' });
    }

    // Route to handler
    switch (action) {
      case 'hoggle-roster':
        return jsonResponse(handleHoggleRoster(body.period || null));

      case 'hoggle-ping':
        return jsonResponse({ success: true, pong: true, timestamp: new Date().toISOString() });

      default:
        return jsonResponse({ success: false, error: 'Unknown action: ' + action });
    }
  } catch (err) {
    return jsonResponse({ success: false, error: err.message });
  }
}

/**
 * Helper: Return JSON response from web app
 */
function jsonResponse(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Get the Hoggle-friendly roster
 *
 * Joins student registry (names, periods) with token registry (anonymous tokens)
 * Returns ONLY: first name + period + anonymous token
 * No student IDs, emails, or last names are included
 *
 * @param {number|null} filterPeriod - Optional period filter
 * @returns {Object} Roster data
 */
function handleHoggleRoster(filterPeriod) {
  // Ensure modules are loaded
  if (typeof _ensureModulesInitialized === 'function') {
    _ensureModulesInitialized();
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Read student registry (hidden_student_registry sheet)
  var registrySheet = ss.getSheetByName('hidden_student_registry');
  if (!registrySheet || registrySheet.getLastRow() < 2) {
    return { success: true, synced: new Date().toISOString(), count: 0, students: [] };
  }

  var registryData = registrySheet.getRange(2, 1, registrySheet.getLastRow() - 1, 5).getValues();
  // Columns: Email | Student ID | Name | Periods | Primary Period

  // Read token registry (hidden_token_registry sheet) for anonymous tokens
  var tokenMap = {}; // studentId → anonymizedToken
  var tokenSheet = ss.getSheetByName('hidden_token_registry');
  if (tokenSheet && tokenSheet.getLastRow() > 1) {
    var tokenData = tokenSheet.getRange(2, 1, tokenSheet.getLastRow() - 1, 2).getValues();
    // Columns: StudentId | AnonymizedToken
    tokenData.forEach(function(row) {
      if (row[0] && row[1]) {
        tokenMap[String(row[0])] = String(row[1]);
      }
    });
  }

  // Build roster
  var students = [];
  var skippedNoToken = 0;

  registryData.forEach(function(row) {
    var studentId = String(row[1]).trim();
    var fullName = String(row[2]).trim();
    var periodsStr = String(row[3]);
    var periods = periodsStr.split(',').map(function(p) { return parseInt(p.trim()); }).filter(function(p) { return !isNaN(p); });

    if (!studentId || !fullName) return;

    // Get anonymous token
    var token = tokenMap[studentId];
    if (!token) {
      // Fallback: generate a simple hash-based skey
      // This ensures all students get an skey even without Overlord tokens
      token = 'skey_' + simpleHash(studentId).substring(0, 8);
      skippedNoToken++;
    }

    // Extract first name only (registry stores "Last, First Middle")
    var firstName = fullName;
    var commaIndex = fullName.indexOf(',');
    if (commaIndex !== -1) {
      firstName = fullName.substring(commaIndex + 1).trim().split(/\s+/)[0];
    }

    // Apply period filter if specified
    var targetPeriods = periods;
    if (filterPeriod) {
      targetPeriods = periods.filter(function(p) { return p === parseInt(filterPeriod); });
    }

    if (targetPeriods.length > 0) {
      students.push({
        skey: token,
        name: firstName,
        periods: targetPeriods,
        primary_period: periods[0]
      });
    }
  });

  return {
    success: true,
    synced: new Date().toISOString(),
    count: students.length,
    students_without_overlord_token: skippedNoToken,
    students: students
  };
}

/**
 * Simple deterministic hash for fallback skeys
 * NOT cryptographic - just for generating consistent anonymous IDs
 */
function simpleHash(str) {
  var hash = 0;
  for (var i = 0; i < str.length; i++) {
    var char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  // Convert to hex string, ensure positive
  return Math.abs(hash).toString(16).padStart(8, '0');
}
