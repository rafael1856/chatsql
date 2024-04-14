"""
This module contains functions for interacting with the OpenAI API.

Functions:
- send_api_request_to_openai_api: Sends a request to the OpenAI API's chat completions endpoint. This function is decorated with a retry mechanism that waits for a random exponential time between attempts and stops after 3 attempts.
- execute_function_call: Executes a function call provided by the OpenAI API's response.

Imports:
- json: Used for handling JSON data.
- requests: Used for sending HTTP requests.
- utils.config: Contains configuration variables for the application.
- utils.database_functions: Contains functions for interacting with the database.
- tenacity: Provides a decorator for adding retry behavior to functions.

Exceptions:
- ConnectionError: Raised when a request to the OpenAI API fails.
"""

#
# TODO: THIS IS THE REFACTORED VERSION OF THE ORIGINAL CODE THAT USED REQUESTS.GET() directly. 
# TODO: EXPLAIN THE CHANGES MADE AND WHY THEY WERE MADE.
# TODO: use this Phind Debug information 
# The RetryError you're encountering indicates that the send_api_request_to_openai_api function, which is decorated with a retry mechanism using tenacity, has failed to execute successfully after the specified number of retry attempts. This could be due to several reasons, such as network issues, incorrect API credentials, or the API endpoint being unavailable.
# Here are steps to troubleshoot and potentially resolve this issue:
# Verify API Credentials and Endpoint: Ensure that the LM_STUDIO_API_KEY and the API endpoint URL (http://localhost:1234/v1) are correct. If you're running the LMStudio server locally, make sure it's up and running.
# Check Network Connectivity: If the LMStudio server is running on a different machine or a container, ensure that your machine can reach it. You can test this by pinging the server's IP address or using a tool like curl to make a request to the API endpoint.
# Review Retry Parameters: The retry mechanism is configured with wait_random_exponential(min=1, max=40) and stop_after_attempt(3). This means it will wait a random amount of time between 1 and 40 seconds between retries and will stop after 3 attempts. You might want to adjust these parameters based on your specific needs and environment.
# Inspect the Exception: Modify the send_api_request_to_openai_api function to print or log the exception that caused the retry mechanism to fail. This can provide more insight into what's going wrong.
# 

import json
import requests
from config import OPENAI_API_KEY, AI_MODEL
from database_functions import ask_postgres_database, postgres_connection
from tenacity import retry, wait_random_exponential, stop_after_attempt

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))


def send_api_request_to_openai_api(messages, functions=None, function_call=None, model=AI_MODEL, openai_api_key=OPENAI_API_KEY):
  """
  Send the API request to the OpenAI API via Chat Completions endpoint.

  Args:
    messages (list): A list of message objects containing 'role' and 'content' keys.
    functions (list, optional): A list of function objects. Defaults to None.
    function_call (dict, optional): A dictionary representing the function call. Defaults to None.
    model (str, optional): The model to use for the API request. Defaults to AI_MODEL.
    openai_api_key (str, optional): The API key for the OpenAI API. Defaults to OPENAI_API_KEY.

  Returns:
    requests.Response: The response object from the API request.

  Raises:
    ConnectionError: If there is a failure to connect to the OpenAI API.
  """
  try:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {openai_api_key}"}
    json_data = {"model": model, "messages": messages}
    if functions: 
      json_data.update({"functions": functions})
    if function_call: 
      json_data.update({"function_call": function_call})
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=json_data)
    response.raise_for_status()

    return response
  
  except requests.RequestException as e:
    raise ConnectionError(f"Failed to connect to OpenAI API due to: {e}")

def execute_function_call(message):
  """
  Run the function call provided by OpenAI's API response.

  Args:
    message (dict): The API response message containing the function call details.

  Returns:
    str: The results of the function call.

  Raises:
    None

  """
  if message["function_call"]["name"] == "ask_postgres_database":
    query = json.loads(message["function_call"]["arguments"])["query"]
    print(f"SQL query: {query} \n")
    results = ask_postgres_database(postgres_connection, query)
    print(f"Results A: {results} \n")
  else:
    results = f"Error: function {message['function_call']['name']} does not exist"
  return results
