from db.database import supabase

def add_entry(user_id, query, casual_response, formal_response):
    try:
        result = supabase.table("prompts").insert({
            "user_id": user_id,
            "query": query,
            "casual_response": casual_response,
            "formal_response": formal_response
        }).execute()
   
        return True

    except Exception as e:
        return e


def get_history(user_id):
    try:
        result = supabase.table("prompts").select("*").eq("user_id",user_id).order("created_at",desc=True).execute()
   
        return (result.data)

    except Exception as e:
        return e

