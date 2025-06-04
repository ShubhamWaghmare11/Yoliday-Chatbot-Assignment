from fastapi import FastAPI, HTTPException, Response, Request
from dotenv import load_dotenv
import json
from langchain_groq import ChatGroq
import groq
from utils.prompts import build_prompt, build_refine_prompt
from schemas import getInput 
from db import crud
import re


load_dotenv()


app = FastAPI()




def extract_json(text: str) -> dict:
    """
    Cleans and parses a string containing JSON content.

    This function removes Markdown-style code block wrappers (e.g., ```json)
    and converts the remaining string into a Python dictionary.

    Args:
        text (str): The raw string response from the model containing JSON.

    Returns:
        dict: Parsed JSON content as a dictionary.

    Raises:
        ValueError: If the string does not contain valid JSON.
    """

    try:
        cleaned = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from model")


@app.post("/generate")
def generate(user_input: getInput):
    """
    Generates AI responses (casual and formal) for a user-provided query.

    This endpoint accepts a query and a GROQ API key, invokes the ChatGroq
    model to generate and refine responses, and stores the interaction in the database.

    Args:
        user_input (getInput): Pydantic model containing `user_id`, `query`, and `groq_api_key`.

    Returns:
        dict: JSON response containing the AI-generated `casual_response` and `formal_response`.

    Raises:
        HTTPException: 
            - 401 if authentication with Groq fails.
            - 500 for any other unexpected errors.
    """

    try:
        model = ChatGroq(model_name='Gemma2-9b-It', api_key=user_input.groq_api_key)
        prompt = build_prompt(user_input.query)
        initial_response = model.invoke(prompt)

        refinement_prompt = build_refine_prompt(initial_response.content)
        refined_response = model.invoke(refinement_prompt)
        
        response_dict = extract_json(refined_response.content)

        crud_response = crud.add_entry(user_input.user_id, user_input.query, response_dict['casual_response'], response_dict['formal_response'])
        print(crud_response)
        return {"output": response_dict}

    except groq.AuthenticationError as e:
        # Send error to frontend with HTTP 401
        raise HTTPException(status_code=401, detail="Invalid Groq API Key. Please check and try again.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



@app.get("/history")
def history(user_id: str):
    """
    Retrieves chat history for a specific user.

    This endpoint returns all past queries and responses associated with the given user,
    ordered by the most recent first.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        dict: A dictionary containing a list of past chat records under the key `"output"`.

    Raises:
        HTTPException: 
            - 500 if the database query fails.
    """

    try:
        history = crud.get_history(user_id) 
        print(history)   
        return {'output':history}


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/health", methods=["GET", "HEAD"])
def health(request: Request):
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok"}
