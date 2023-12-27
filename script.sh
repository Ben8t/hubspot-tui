#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# curl -X GET \
#   'https://api.hubapi.com/crm/v3/objects/contacts' \
#   -H "Authorization: Bearer $HS_API_TOKEN" \
#   -H "Content-Type: application/json"


# curl -X GET \
#   'https://api.hubapi.com/crm/v3/objects/deals' \
#   -H "Authorization: Bearer $HS_API_TOKEN" \
#   -H "Content-Type: application/json"


selected_props=$(cat props.txt | gum choose --limit 2)

IFS=$'\n' read -r -d '' -a props_array <<< "$selected_props"

# Generate the JSON payload based on user input for each property
json_payload='{
  "associations": {
    "associatedVids": [
      51
    ]
  },
  "properties": [
'

# Iterate through each property in the array and prompt for the value using gum input
for prop in "${props_array[@]}"; do
  value_prop=$(gum input --placeholder "$prop")
  json_payload+='{
      "value": "'"$value_prop"'",
      "name": "'"$prop"'"
    },'
done

json_payload=${json_payload%,}
json_payload+='
  ]
}'

# Print the generated JSON payload (for testing purposes)
echo "$json_payload"

# Execute the curl command with the generated JSON payload
url='https://api.hubapi.com/deals/v1/deal'
curl -X POST "$url" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $HS_API_TOKEN" \
-d "$json_payload"