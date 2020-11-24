
DOMAIN = "bryx911"

TYPE_KEEP_ALIVE = 9
# {
# 	"type": 5,
# 	"topic": "jobs",
# 	"data": {
# 		"id": "1:5fb430507ef26fd7b54dc27b:newJob:5fb428a64b1f610c4cfd9596",
# 		"job": {
# 			"id": "5fb430507ef26fd7b54dc27b",
# 			"ts": 1605644365,
# 			"disposition": "open",
# 			"synopsis": "GENERAL FIRE ALARM, ZONE 1. OPP#21",
# 			"unitShortNames": ["F_ONTARIO2"],
# 			"type": {
# 				"id": "ALARM",
# 				"code": "ALARM",
# 				"type": "fire",
# 				"section": "FIRE",
# 				"description": "ALARM ACTIVATION",
# 				"_id": "ALARM",
# 				"desc": "ALARM ACTIVATION"
# 			},
# 			"address": {
# 				"original": "2102 BROWN SQ",
# 				"street": "2102 BROWN SQ",
# 				"state": "NY",
# 				"locationInfo": "BROWN SQUARE VILLAGE APTS - 2102"
# 			},
# 			"centroid": {
# 				"properties": {},
# 				"type": "Point",
# 				"coordinates": [-77.27977035, 43.22183925]
# 			},
# 			"hasResponded": false
# 		},
# 		"type": "new"
# 	}
# }
TYPE_UPDATE_PUSH = 5

# {
# 	"type": 6,
# 	"topic": "jobs",
# 	"id": 105,
# 	"data": {
# 		"type": "ack",
# 		"updateIds": ["1:5fb430507ef26fd7b54dc27b:newJob:5fb428a64b1f610c4cfd9596"]
# 	}
# }
TYPE_ACK = 6
TYPE_INITAL_JOBS = 1

CONF_API_KEY = 'api_key'
