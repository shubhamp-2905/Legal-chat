# import google.generativeai as genai
# from app.config import GEMINI_API_KEY

# class GeminiAnswerer:
#     def __init__(self):
#         genai.configure(api_key=GEMINI_API_KEY)
#         self.model = genai.GenerativeModel("gemini-2.0-flash")

#     def format_answer(self, context_chunks, question):
#         prompt = f"""
#         You are a legal assistant specializing in Indian law. Use the context to answer the question clearly and accurately.

#         Context:
#         {chr(10).join(['- ' + chunk for chunk in context_chunks])}

#         Question: {question}

#         Answer in a clear, professional legal tone.
#         """
#         response = self.model.generate_content(prompt)
#         return response.text.strip()
    
    
