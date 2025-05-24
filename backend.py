from fastapi import FastAPI, HTTPException
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
    try:
        cleaned = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from model")


@app.post("/generate")
def generate(user_input: getInput):
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
    try:
        history = crud.get_history(user_id) 
        print(history)   
        return {'output':history}


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
