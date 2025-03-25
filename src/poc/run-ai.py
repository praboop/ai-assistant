from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Load pre-trained sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Example past discussions stored with problem threads
past_discussions = {
    "Server is not responding": {
        "responses": [
            "Try restarting the server.",
            "Check if the firewall is blocking the requests.",
            "Restarting fixed the issue."
        ],
        "accepted_solution": "Restart the server and check the logs for errors."
    },
    "Database connection failed": {
        "responses": [
            "Check database credentials.",
            "Is the network stable?",
            "Fixed after correcting database config."
        ],
        "accepted_solution": "Check database credentials and network connectivity."
    },
    "High CPU usage detected": {
        "responses": [
            "Monitor the system load.",
            "Try optimizing your SQL queries."
        ],
        "accepted_solution": "Optimize queries and check running processes."
    }
}

# Prepare embeddings for problem statements + thread discussions
past_statements = list(past_discussions.keys())
past_solutions = {problem: details["accepted_solution"] for problem, details in past_discussions.items()}
past_embeddings = model.encode(past_statements)

# Index embeddings in FAISS for efficient search
dimension = past_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(past_embeddings))

# Similarity threshold for matching (lower means stricter matching)
SIMILARITY_THRESHOLD = 0.5

# Function to analyze and find solutions for new problem threads
def analyze_problem_thread(problem, thread_responses):
    new_embedding = model.encode([problem])
    D, I = index.search(np.array(new_embedding), 1)  # Get top 1 match

    print(f"\nProblem: {problem}")
    
    if D[0][0] < SIMILARITY_THRESHOLD:
        matched_problem = past_statements[I[0][0]]
        print(f"→ Similar Issue Found: {matched_problem}")
        print(f"→ Suggested Solution: {past_solutions[matched_problem]}")
        print(f"→ Previous Discussion Thread: {past_discussions[matched_problem]['responses']}\n")
    else:
        print("→ No similar issue found. Escalating to a human expert.")

    # Learn from new responses in the thread
    if thread_responses:
        print("→ New Discussion in the Thread:")
        for response in thread_responses:
            print(f"  - {response}")
        
        # If the submitter confirms a fix, update knowledge base
        if "fixed" in " ".join(thread_responses).lower():
            accepted_fix = thread_responses[-1]  # Assume last response is the final solution
            past_discussions[problem] = {
                "responses": thread_responses,
                "accepted_solution": accepted_fix
            }
            print(f"→ Learning from thread: Marking as solved with solution: {accepted_fix}\n")

# Define new problem threads at the end and call analysis
new_problem_threads = [
    {
        "problem": "Server is not responding",
        "thread_responses": [
            "Checked the logs, nothing seems off.",
            "Restarted the service, now it works."
        ]
    },
    {
        "problem": "Application crashes unexpectedly",
        "thread_responses": [
            "Seems like a memory issue.",
            "Debugging now, will update."
        ]
    }
]

# Analyze each new problem thread
for thread in new_problem_threads:
    analyze_problem_thread(thread["problem"], thread["thread_responses"])
