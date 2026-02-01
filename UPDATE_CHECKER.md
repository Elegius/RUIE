# RUIE Update Checker - Documentation

**Version**: 0.2 Alpha  
**Date**: February 1, 2026  
**Status**: ✅ Implemented and Active

---

## Overview

RUIE includes an automatic update checking system that monitors GitHub for new releases. Users are notified when updates become available, making it easy to stay current with the latest features and security patches.

---

## Features

### ✅ Automatic Background Checking
- Checks for updates automatically when the application launches
- Performs periodic checks every 24 hours while the app is running
- Non-blocking: checks happen asynchronously without interrupting user workflow
- Silent failure: if the check fails (no network, etc.), the app continues normally

### ✅ Visual Update Notification
When an update is available:
- A prominent banner appears at the top of the application
- Shows the new version number
- Displays release notes excerpt (first 500 characters)
- Includes a "Download" button linking to the GitHub release page
- Includes a "Dismiss" button to close the notification

### ✅ GitHub Integration
- Queries the official GitHub API: `https://api.github.com/repos/Elegius/RUIE/releases/latest`
- No authentication required (public repository)
- Respects GitHub's API rate limits (60 requests per hour per IP)
- Timeout protection: 5-second timeout prevents hanging

### ✅ Version Comparison
- Compares current version with latest GitHub release version
- Works with semantic versioning (e.g., "0.2" vs "0.3")
- Simple string comparison (lexicographic ordering)
- Handles pre-release versions

---

## Implementation Details

### Backend API Endpoints

#### `/api/check-updates` (GET)
**Purpose**: Check for the latest version on GitHub  
**Returns**: JSON response with update information

**Success Response** (200 OK):
```json
{
    "success": true,
    "current_version": "0.2 Alpha",
    "latest_version": "0.3 Beta",
    "has_update": true,
    "release_url": "https://github.com/Elegius/RUIE/releases/tag/v0.3",
    "release_notes": "New features: automatic installation, theme marketplace..."
}
```

**Network Error Response** (200 OK - graceful degradation):
```json
{
    "success": true,
    "current_version": "0.2 Alpha",
    "latest_version": "0.2 Alpha",
    "has_update": false,
    "error": "Could not check updates: [Network error details]"
}
```

#### `/api/app-version` (GET)
**Purpose**: Get the current application version  
**Returns**: JSON with version info

**Response** (200 OK):
```json
{
    "success": true,
    "version": "0.2 Alpha"
}
```

### Frontend Implementation

#### JavaScript Functions

**`checkForUpdates()`**
- Async function that calls `/api/check-updates`
- Parses the response
- Calls `showUpdateNotification()` if update is available
- Silently catches and logs any errors

**`showUpdateNotification(latestVersion, releaseUrl, releaseNotes)`**
- Creates or updates the update banner element
- Styles the banner with a gradient background
- Adds Download and Dismiss buttons
- Adjusts page layout to accommodate the banner

#### Initialization
- Initial check: 2 seconds after page loads (allowing UI to settle)
- Recurring checks: Every 24 hours (86,400,000 milliseconds)
- Non-blocking: Uses `setTimeout()` and `setInterval()` for async execution

---

## User Experience

### When App Starts
1. User opens RUIE application
2. UI loads normally (2-second delay for first update check)
3. App queries GitHub in the background
4. If update is available, notification appears at top
5. User can click "Download" to visit the release page or "Dismiss" to close

### Subsequent Sessions
- Check repeats automatically every 24 hours
- Only shows notification if a new update is found
- Can manually check by visiting: https://github.com/Elegius/RUIE/releases

### Network Issues
- If GitHub is unreachable, no error is shown to user
- Update check simply fails silently
- App continues to function normally
- User can manually check GitHub for updates

---

## Configuration

### Checking Interval
Located in `public/app.js` at the `window.addEventListener('load')` section:

```javascript
// Check for updates asynchronously (non-blocking)
setTimeout(() => {
    checkForUpdates();
}, 2000); // Wait 2 seconds after app loads

// Check for updates every 24 hours
setInterval(checkForUpdates, 24 * 60 * 60 * 1000);
```

To modify:
- **First check delay**: Change `2000` (milliseconds) to desired value
- **Recurring check interval**: Change `24 * 60 * 60 * 1000` to desired milliseconds
  - 1 hour = `60 * 60 * 1000` = 3,600,000 ms
  - 12 hours = `12 * 60 * 60 * 1000` = 43,200,000 ms

### GitHub API Endpoint
Located in `server.py` in the `api_check_updates()` function:

```python
url = 'https://api.github.com/repos/Elegius/RUIE/releases/latest'
```

To point to a different repository:
- Change the repository path: `repos/OWNER/REPO`
- Ensure the repository is public
- Ensure it has GitHub releases configured

### Timeout
Located in `server.py`:

```python
with urllib.request.urlopen(req, timeout=5) as response:
```

To modify timeout (seconds), change the `timeout=5` value.

---

## Privacy & Security

### Data Sent to GitHub
When checking for updates, the following happens:
1. A GET request is sent to GitHub's public API
2. Only the repository path is transmitted (no user data)
3. GitHub may log the IP address (standard web server logging)
4. No authentication credentials are sent
5. No personal information is transmitted

### GitHub Terms
- Uses GitHub's public API within their free tier
- Complies with GitHub API terms of service
- Rate limited to 60 requests per hour per IP (more than sufficient)

### Security Considerations
- Checks use HTTPS (secure connection)
- Timeout prevents hanging on network issues
- No automatic downloads (user must manually click)
- User must manually download and install updates
- Respects GitHub's User-Agent requirements (included in request)

---

## Testing

### Manual Testing

**Test 1: Check API Endpoint Directly**
```bash
# From browser console or command line
fetch('/api/check-updates').then(r => r.json()).then(console.log)

# Should return current and latest version info
```

**Test 2: Check App Version**
```bash
fetch('/api/app-version').then(r => r.json()).then(console.log)
```

**Test 3: Force Update Check**
In browser console:
```javascript
checkForUpdates();
```

### Testing with Network Issues
- Disconnect from network before starting app
- Check that app loads normally without errors
- Update check fails silently
- Reconnect and check that next check works

### Testing Version Comparison
Edit version numbers in testing:
- Current: "0.2 Alpha" → Set to lower version for testing
- Latest: Create a test release on GitHub with higher version
- Should show update notification

---

## Troubleshooting

### Update Notification Never Appears
**Possible causes:**
1. No internet connection (app continues anyway)
2. GitHub API is down
3. You're already on the latest version
4. Browser console shows no errors

**Solution:**
1. Check your internet connection
2. Try manually visiting: https://github.com/Elegius/RUIE/releases
3. Check browser console (F12) for any JavaScript errors
4. Try restarting the application

### Update Notification Shows Old Version
**Possible causes:**
1. GitHub release hasn't been created yet
2. Release is marked as a draft (not published)
3. Release tag doesn't follow expected format

**Solution:**
1. Ensure release is fully published (not draft)
2. Check that release tag starts with 'v' (e.g., 'v0.3')
3. Wait a few minutes for GitHub API to update

### Network Timeout
**Possible causes:**
1. Slow internet connection
2. GitHub API is experiencing high load
3. ISP blocking GitHub

**Solution:**
1. Check internet speed
2. Wait a moment and try again
3. Try using VPN if ISP blocks GitHub

---

## Future Enhancements

### Planned for v0.3+
- Automatic downloads (not just notification)
- Update installation without restarting
- Release notes displayed in-app (not just excerpt)
- Option to opt-out of update checks
- Settings page to configure update check frequency
- Changelog view in the application

### Long-term Vision
- Self-contained update installer
- Delta updates (only download changed files)
- Beta release channel option
- Rollback to previous version functionality

---

## API Reference

### `/api/check-updates` 

**Method**: GET  
**Authentication**: None  
**Rate Limit**: Implicit (GitHub API 60 req/hr)  
**Timeout**: 5 seconds  

**Request**:
```
GET /api/check-updates HTTP/1.1
Host: localhost:5000
```

**Response** (Success - 200):
```json
{
    "success": true,
    "current_version": "string",
    "latest_version": "string",
    "has_update": boolean,
    "release_url": "string",
    "release_notes": "string (max 500 chars)"
}
```

**Response** (Network Error - 200):
```json
{
    "success": true,
    "current_version": "string",
    "latest_version": "string",
    "has_update": false,
    "error": "string describing the error"
}
```

**Response** (Server Error - 500):
```json
{
    "success": false,
    "error": "string describing the error"
}
```

---

## Files Modified

| File | Changes |
|------|---------|
| `server.py` | Added `/api/check-updates` and `/api/app-version` endpoints |
| `public/app.js` | Added `checkForUpdates()` and `showUpdateNotification()` functions |
| `RELEASE_SUMMARY.md` | Updated features list to include Update Checker |
| `STATUS.md` | Moved auto-update from future features to completed v0.2 |
| `INSTALL_GUIDE.md` | Updated with automatic update checking information |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 1, 2026 | Initial implementation |

---

**Created**: February 1, 2026  
**Status**: ✅ Complete and Active  
**Maintenance**: Requires no maintenance - GitHub integration is automatic
