from runner import SandboxStorage

storage = SandboxStorage("data")
user_id = "user_123"

memory = [
    {"role": "user", "content": "Write a simple function. In our project it is strictly forbidden to use SharedPreferences, we only use DataStore."},
    {"role": "coder", "content": "Ok, I wrote the code and used DataStore as you requested."},
    {"role": "reviewer", "content": "APPROVE. The code is excellent, using DataStore meets our standards."}
]

print("Extracting facts...")
storage.ingest_and_extract_facts(user_id, memory)
print("Done!")
