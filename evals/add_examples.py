from dotenv import load_dotenv
from langsmith import Client


DATASET_NAME = "researchlens-v1-eval"


def main():
    load_dotenv()

    client = Client()
    dataset = client.read_dataset(dataset_name=DATASET_NAME)

    examples = [
        {
            "inputs": {
                "query": (
                    "In AWS SDK configuration, what decides which one wins "
                    "when several credential sources are available?"
                )
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Use indexed documentation, and rewrite/retry if the first "
                    "retrieval does not surface credential precedence clearly."
                ),
            },
        },
        {
            "inputs": {
                "query": (
                    "What changed recently in AWS SDK credential source precedence?"
                )
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "Use recent web evidence and avoid relying only on the "
                    "indexed documentation."
                ),
            },
        },
    ]

    client.create_examples(dataset_id=dataset.id, examples=examples,)

    print("Added 2 examples.")


if __name__ == "__main__":
    main()