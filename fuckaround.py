import os
import pandas as pd
import openai
import psycopg2
from glob import glob

openai.api_key = "API_Key"

DB_NAME = "xxxxx"
DB_USER = "xxxxxx"
DB_PASSWORD = "xxxxx"
DB_HOST = "localhost"
DB_PORT = "xxxxx"

def classify_review(review):
    prompt = f"""
    Given the following user review, classify it into the following categories:
    - Bug Report: High, Medium, Low, No
    - Improvement Request: High, Medium, Low, No
    - Rating: High, Medium, Low, No
    - Others: High, Medium, Low, No

    Review: "{review}"
    
    Return the result in the format:
    Bug Report: [value]
    Improvement Request: [value]
    Rating: [value]
    Others: [value]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful AI assistant."},
                      {"role": "user", "content": prompt}]
        )
        result = response["choices"][0]["message"]["content"]
        lines = result.split("\n")

        return {
            "bug_report": lines[0].split(": ")[1],
            "improvement_request": lines[1].split(": ")[1],
            "rating": lines[2].split(": ")[1],
            "others": lines[3].split(": ")[1]
        }

    except Exception as e:
        print("Error in classification:", e)
        return {"bug_report": "No", "improvement_request": "No", "rating": "No", "others": "No"}

def connect_db():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

files = glob("set_*.xlsx")
all_data = []

for file in files:
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        review_text = row["review"]
        classification = classify_review(review_text)
        
        all_data.append({
            "review": review_text,
            "bug_report": classification["bug_report"],
            "improvement_request": classification["improvement_request"],
            "rating": classification["rating"],
            "others": classification["others"]
        })

output_df = pd.DataFrame(all_data)
output_df.to_excel("classified_reviews.xlsx", index=False)

try:
    conn = connect_db()
    cur = conn.cursor()

    for data in all_data:
        cur.execute("""
            INSERT INTO reviews (review, bug_report, improvement_request, rating, others) 
            VALUES (%s, %s, %s, %s, %s);
        """, (data["review"], data["bug_report"], data["improvement_request"], data["rating"], data["others"]))

    conn.commit()
    cur.close()
    conn.close()
    print("Data successfully inserted into PostgreSQL!")

except Exception as e:
    print("Database Error:", e)
