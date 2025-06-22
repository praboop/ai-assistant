import argparse
from query_service import get_thread_response

def main():
    parser = argparse.ArgumentParser(description="Query → Thread Response Assistant")
    parser.add_argument("query", type=str, help="Natural language query")
    args = parser.parse_args()

    response = get_thread_response(args.query)

    if response:
        print("\n🧠 Based on similar queries, here's a relevant answer from a past thread:\n")
        print("---")
        print(f"Q: {args.query}")
        print(f"A: {response['answer']}\n")
        if response.get("follow_ups"):
            for i, follow_up in enumerate(response["follow_ups"], 1):
                print(f"Follow-up {i}: {follow_up}")
        print(f"Source thread: {response['thread_id']}")
    else:
        print("❌ No relevant past thread found.")

if __name__ == "__main__":
    main()
