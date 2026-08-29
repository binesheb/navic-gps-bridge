# NavIC-GPS Bridge API

## Live data
`GET /api/live`

Returns the latest parsed fix, navigation values, freshness state and satellite view.

## Diagnostics
`GET /api/diagnostics`

Returns uptime, heap, packet counters and connected TCP clients.

## Configuration
`GET /api/config`

`POST /api/config`

Example:
```json
{
  "gnss_baud": 9600,
  "gps_output_baud": 9600,
  "gps_compatibility": true
}
```

A restart is required after serial configuration changes.

## Track logging
`GET /api/track`

Returns the rolling in-memory track buffer.

`POST /api/track/clear`

Clears the current track.

`GET /api/track.csv`

Downloads the rolling track as CSV.

## System actions
`POST /api/config/reset`

`POST /api/system/restart`
