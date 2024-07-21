import os
import fitz  # PyMuPDF library for PDF parsing
import time
from crewai import Agent, Crew, Task, Process
import openai
import tkinter as tk
from tkinter import scrolledtext

# Set environment variables for API access
os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
os.environ["OPENAI_MODEL_NAME"] = "llama3-70b-8192"
os.environ["OPENAI_API_KEY"] = "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"

# Define the Explanation Generator Agent
explanation_generator = Agent(
    role='Ai wine assistant',
    goal='to provide detailed detail about wine in 20-40 words',
    backstory='you are an AI wine assistant.',
    verbose=True,
    allow_delegation=False
)

# Initialize the chat history and PDF content
chat_history = []
pdf_content = ""

def parse_pdf(file_path="Corpus.pdf"):
    global pdf_content
    pdf_content = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            pdf_content += page.get_text()
        print("PDF content successfully parsed.")
    except Exception as e:
        print(f"Error parsing PDF: {e}")

def truncate_input(input_text, max_length=4000):
    return input_text[:max_length]

def generate_explanation(question):
    global pdf_content
    context = f"{pdf_content}\n\n{chat_history}"
    truncated_context = truncate_input(context)

    generate_explanation_task = Task(
        description=f"if question is not related to {truncated_context} reply (ask business for the question) generate an explanation for the following question: {question} with the context: {truncated_context}.",
        agent=explanation_generator,
        expected_output="short, to-the-point explanation of the topic"
    )

    crew = Crew(
        agents=[explanation_generator],
        tasks=[generate_explanation_task],
        verbose=2,
        process=Process.sequential
    )

    retry_count = 0
    max_retries = 3
    while retry_count < max_retries:
        try:
            output = crew.kickoff()
            return output
        except openai.RateLimitError as e:
            retry_count += 1
            wait_time = 60 * (2 ** retry_count)  # Exponential backoff
            print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    return "Sorry, I am currently experiencing high demand. Please try again later."

def update_chat_history(user_input, bot_response):
    chat_history.append({"user": user_input, "bot": bot_response})
    chat_display.insert(tk.END, f"You: {user_input}\nAI Wine assistant: {bot_response}\n\n")
    chat_display.see(tk.END)

def simulate_typing(bot_response, delay=0.05):
    chat_display.insert(tk.END, "AI Wine assistant is typing...\n")
    chat_display.see(tk.END)
    chat_display.update_idletasks()
    
    time.sleep(1)  
    
    chat_display.delete("end-2l", "end-1l")
    for char in bot_response:
        chat_display.insert(tk.END, char)
        chat_display.update_idletasks()
        time.sleep(delay)
    chat_display.insert(tk.END, "\n\n")
    chat_display.see(tk.END)

def on_send_click():
    user_input = user_entry.get()
    if user_input.lower() in ["exit", "quit"]:
        root.quit()
    else:
        user_entry.delete(0, tk.END)
        chat_display.insert(tk.END, f"You: {user_input}\n")
        chat_display.insert(tk.END, "AI Wine assistant is typing...\n")
        chat_display.see(tk.END)
        chat_display.update_idletasks()
        root.after(100, generate_response, user_input)  # Delay response generation for typing effect

def generate_response(user_input):
    chat_display.delete("end-2l", "end-1l")
    bot_response = generate_explanation(user_input)
    simulate_typing(bot_response)
    update_chat_history(user_input, bot_response)

def on_enter_key(event):
    on_send_click()

# Set up the Tkinter interface
root = tk.Tk()
root.title("AI Wine Assistant")

chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
chat_display.pack(padx=10, pady=10)

user_entry = tk.Entry(root, width=50)
user_entry.pack(padx=10, pady=5)
user_entry.bind("<Return>", on_enter_key)

send_button = tk.Button(root, text="Send", command=on_send_click)
send_button.pack(padx=10, pady=5)

parse_pdf()  

root.mainloop()
