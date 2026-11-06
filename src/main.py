
from src.crm_processor import process_crm_files


def main():
    print("=" * 50)
    print("       AI-POWERED CRM DATA ENTRY ASSISTANT")
    print("=" * 50)

    process_crm_files(limit=None)

    print("\nCRM automation process finished.")
    print("Check the outputs folder for generated CSV files.")


if __name__ == "__main__":
    main()
