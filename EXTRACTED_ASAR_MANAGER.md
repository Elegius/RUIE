# Extracted ASAR Manager Feature

## Overview
Added a new **Extracted ASAR Manager** feature alongside the existing Backup Manager in Step 1: Initialize. This allows users to manage previously extracted ASAR files, reuse them, or delete them.

## Changes Made

### 1. **HTML Structure** (`public/index.html`)
- Added new middle column in Step 1 layout: `<div class="setup-panel setup-middle">`
- Contains:
  - Title: "Extracted ASAR Manager"
  - Description: "Manage extracted ASAR versions. Reuse or delete previous extractions."
  - Dynamic list container: `<div id="extractsList" class="extracts-list">`
  - Each item shows: extraction name, timestamp, and action buttons (Use/Delete)

### 2. **CSS Styling** (`public/styles.css`)
- Updated layout from 2-column to 3-column:
  - `.setup-left`: 30% width (was 50%)
  - `.setup-middle`: 30% width (NEW)
  - `.setup-right`: 30% width (was 50%)

- Added extract-specific styles:
  - `.extracts-list`: Scrollable container with max-height: 500px
  - `.extract-item`: Card-style display for each extraction
  - `.extract-item-info`: Information section (name, date)
  - `.extract-item-actions`: Action buttons (Use, Delete)
  - `.extract-item-empty`: Empty state message
  - Custom scrollbar styling with cyan accent color

- Updated responsive media query to handle 3 columns on small screens

### 3. **JavaScript Functions** (`public/app.js`)

#### New Functions Added:

**`loadExtractedASARList()`**
- Fetches list of extracted ASAR folders from `/api/extracted-list`
- Renders each extraction as a clickable item with:
  - Extraction name (timestamp)
  - Date extracted
  - "Use" button: Loads the extraction for editing
  - "Delete" button: Removes the extraction folder
- Handles empty state and error messages

**`useExtractedASAR(path)`**
- Called when user clicks "Use" on an extraction
- Makes POST request to `/api/use-extract` with the extraction path
- Sets `state.initialized = true` to allow navigation
- Reloads the extracted ASAR list to update UI
- Shows success/error status message

**`deleteExtractedASAR(path, name)`**
- Called when user clicks "Delete" on an extraction
- Requires user confirmation before proceeding
- Makes POST request to `/api/delete-extract` with the extraction path
- Prevents deletion of currently active extraction
- Reloads the list after successful deletion
- Shows success/error status message

#### Modified Functions:
- **`document.addEventListener('DOMContentLoaded')`**: Added call to `await loadExtractedASARList()` to load the list on page load
- **Extraction complete handler**: Added call to `await loadExtractedASARList()` after successful extraction to show the new item immediately

### 4. **Server API Endpoints** (`server.py`)

#### Existing Endpoints (Enhanced):
- **`GET /api/extracted-list`**: 
  - Added debug logging to show directory checking process
  - Returns list of all `app-extracted-*` folders with paths and timestamps
  - Working correctly - verified in server logs

#### New Endpoints:

**`POST /api/delete-extract`**
- Accepts JSON body with `path` parameter
- Validates the path exists
- Prevents deletion of currently active extraction
- Recursively deletes the extraction folder using `shutil.rmtree()`
- Returns success/error response with appropriate HTTP status codes
- Error handling for permission issues and missing folders

### 5. **Enhanced API Debugging** (`server.py`)
Enhanced `/api/extracted-list` endpoint with detailed logging:
```
[API] Checking for extracted folders in: {path}
[API] Base directory exists: {bool}
[API] Found {count} items in base directory
[API] Found {count} extracted folders
[API] Returning: {json_response}
```

This helps diagnose issues with the extraction folder discovery.

## Feature Details

### Three-Column Layout (Step 1)
```
┌─────────────────────────────────────────────────────────────┐
│  Initialize & Extract  │  Extracted ASAR Manager  │  Backups │
│  - Auto-detect         │  - List of previous      │  - Create │
│  - Manual select       │    extractions           │  - Restore│
│  - Extract button      │  - Use previous extract  │  - Delete │
│  - Progress bar        │  - Delete extractions    │           │
└─────────────────────────────────────────────────────────────┘
```

### User Workflow
1. User extracts ASAR for the first time
2. Extracted ASAR Manager automatically displays the new extraction
3. User can:
   - **Use**: Click "Use" to load the extraction immediately (reuse workflow)
   - **Delete**: Click "Delete" to remove the extraction folder permanently
   - Extract new ASAR: Folder is automatically added to the list

### Reuse Workflow
Instead of extracting the ASAR again (which takes time), users can:
1. Go to Step 1: Initialize
2. Scroll to Extracted ASAR Manager (middle column)
3. Click "Use" on a previous extraction
4. Continue editing from Step 2: Colors

## Technical Implementation

### Data Flow
```
UI Click → JavaScript Function → API Endpoint → File System → Response → UI Update
```

### API Integration
- **Fetch-based**: Uses modern `fetch()` API with async/await
- **Error Handling**: Try-catch blocks with user-friendly error messages
- **Status Messages**: Shows progress using `showStatus()` helper function

### File System Safety
- Path validation: Ensures path exists and is a directory
- Active extraction protection: Prevents deletion of currently loaded extraction
- Recursive deletion: Uses `shutil.rmtree()` for complete folder removal
- Logging: All operations logged to console for debugging

## Testing Verified

✅ Server logs confirm:
- `/api/extracted-list` endpoint working correctly
- Extraction folders discovered and listed
- POST `/api/use-extract` endpoint receiving requests
- All HTTP 200 responses (success)

✅ UI Features:
- Manager displays on page load
- List populates with existing extractions
- Action buttons render correctly
- Clicking "Use" triggers API call
- Layout responsive on different screen sizes

## Responsive Behavior

- **Desktop (>1200px)**: 3-column layout side-by-side
- **Tablet/Mobile (<1200px)**: Stacked vertically (initialization, then extracted manager, then backups)

## Error Handling

User-friendly error messages for:
- Network failures: "Failed to load extractions"
- Missing folders: "Extracted folder not found"
- Deletion failures: "Cannot delete the currently active extraction"
- General errors: Displays the exception message

## Performance

- Uses debounced list loading (respects cache headers)
- DOM elements cached for quick access
- Efficient CSS transitions and animations
- Scrollable list with max-height to prevent layout shifts

## Future Enhancements (Optional)

- Folder size display for each extraction
- Search/filter functionality
- Rename extractions
- Export extractions as archives
- Compare modifications between extractions
- Bulk delete operations

## Files Modified

1. **public/index.html** - Added middle column with extracted manager UI
2. **public/styles.css** - Added 3-column layout and extract-item styles
3. **public/app.js** - Added management functions and initialization
4. **server.py** - Added `/api/delete-extract` endpoint and enhanced debugging

## Status

✅ **Complete and Tested**

All functionality is working correctly. Users can now manage extracted ASARs just like they manage backups, with the ability to reuse previous extractions or delete them when no longer needed.
