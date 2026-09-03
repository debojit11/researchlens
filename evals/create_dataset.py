from dotenv import load_dotenv
from langsmith import Client


DATASET_NAME = "researchlens-v1-eval"


def main():
    load_dotenv()

    client = Client()

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "Evaluation dataset for ResearchLens adaptive RAG routing, "
            "retrieval, correction, web fallback, and answer quality."
        ),
    )

    examples = [
        {
            "inputs": {
                "query": "How does AWS SDK credential resolution work?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Explain how AWS SDK credential resolution works, including "
                    "the credential provider chain and how valid credentials are selected."
                ),
            },
        },
        {
            "inputs": {
                "query": "What is the AWS credential provider chain?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Explain what the AWS credential provider chain is and how it "
                    "searches credential sources in order."
                ),
            },
        },
        {
            "inputs": {
                "query": "How does AWS_PROFILE affect SDK configuration?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Explain how AWS_PROFILE influences AWS SDK configuration and "
                    "profile selection using the correct technical terminology."
                ),
            },
        },
        {
            "inputs": {
                "query": "Where can AWS SDK credentials be configured?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Describe the main locations and mechanisms through which AWS SDK "
                    "credentials can be configured or resolved."
                ),
            },
        },
        {
            "inputs": {
                "query": "How are retry settings configured in AWS SDKs?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Explain how retry behavior or retry settings are configured in AWS SDKs."
                ),
            },
        },
        {
            "inputs": {
                "query": "What changed in AWS SDK authentication this week?"
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "Summarize AWS SDK authentication-related changes that occurred "
                    "within the requested recent time window, and avoid presenting "
                    "older changes as changes from this week."
                ),
            },
        },
        {
            "inputs": {
                "query": "What are the latest AWS SDK credential changes?"
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "Summarize the latest AWS SDK credential-related changes and clearly "
                    "distinguish recent changes from older background information."
                ),
            },
        },
        {
            "inputs": {
                "query": "What is the latest stable version of the AWS SDK for Java?"
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "State the current stable AWS SDK for Java version and include "
                    "the release date if supported by the evidence."
                ),
            },
        },
        {
            "inputs": {
                "query": "What decides which credential source gets used?"
            },
            "outputs": {
                "expected_route": "documentation",
                "expected_behavior": (
                    "Explain the precedence or ordering rules that determine which "
                    "credential source is selected."
                ),
            },
        },
        {
            "inputs": {
                "query": "Explain how Django middleware works."
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "Clearly explain how Django middleware works, including its role "
                    "in the request and response lifecycle."
                ),
            },
        },
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
                    "Explain the AWS SDK credential precedence rules when multiple "
                    "credential sources are available."
                ),
            },
        },
        {
            "inputs": {
                "query": "What changed recently in AWS SDK credential source precedence?"
            },
            "outputs": {
                "expected_route": "web",
                "expected_behavior": (
                    "Describe recent changes specifically related to AWS SDK credential "
                    "source precedence, staying within the scope of AWS SDKs rather than "
                    "substituting a different SDK or related library."
                ),
            },
        },
    ]

    client.create_examples(dataset_id=dataset.id, examples=examples)

    print(f"Created dataset: {dataset.name}")
    print(f"Examples: {len(examples)}")


if __name__ == "__main__":
    main()