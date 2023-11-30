#!/bin/bash

# set up variables
input_file="input.csv"
output_file="output.csv"
api_url="http://localhost:8000/call/input"

echo "building app, please wait"
# start API app
docker-compose up -d

# wait for API app to be ready
until $(curl --silent --output /dev/null --fail http://localhost:8000/); do
  printf '.'
  sleep 10
done
echo "API is up and running!"

# clear output file
echo "input,output" > "$output_file"

echo "starting script"
# loop through input file
while read input || [ -n "$input" ]; do
  # make API call
  echo ""
  echo "- processing input: "
  echo $input
  output=$(curl -s -X POST "$api_url" -H "Content-Type: application/json" -d "{\"input\": \"$input\"}")
  # add input and output to output file
  echo "- output: "
  echo $output
  echo ""
  echo "\"$input\",\"$output\"" >> "$output_file"
done < "$input_file"

# stop API app
docker-compose down