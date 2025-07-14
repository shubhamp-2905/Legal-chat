# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from dotenv import load_dotenv
# import streamlit as st
# import os

# load_dotenv()
# HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")

# # st.header("ChatBot")

# # ✅ Use a proper chat model
# llm = HuggingFaceEndpoint(
#     repo_id="Johnyquest7/thyroid_open_llama_3b_v2b_full",
#     task="text-generation",
#     huggingfacehub_api_token=HUGGINGFACE_TOKEN
# )

# model = ChatHuggingFace(llm=llm)

# chat_history = []

# while True:
#     user_input = input("You : ")
#     chat_history.append(user_input)
#     if user_input==exit:
#         break
#     result = model.invoke(chat_history)
#     chat_history.append(result.content)
#     print("AI :", result.content)  

# print(chat_history)
  
