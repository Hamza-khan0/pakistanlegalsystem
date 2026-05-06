from app.db.session import SessionLocal
from app.services.tier1_data.dataset_builder import build_tier1_datasets
from app.services.tier1_data.export_bundle import export_training_bundle
from app.services.tier1_data.importer import import_huggingface, import_kaggle, import_local


def _print_result(title: str, result: dict) -> None:
    print(f"\n{title}: {result.get('status')} - {result.get('message')}")
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")


def main() -> None:
    with SessionLocal() as db:
        _print_result("Local import", import_local(db))
        _print_result("Kaggle import", import_kaggle(db))
        _print_result("Hugging Face import", import_huggingface(db))
        datasets = build_tier1_datasets(db)
        print(f"\nDatasets: {datasets['message']}")
        for item in datasets["datasets"]:
            print(f"{item['taskName']}: {item['recordCount']} records")
        for warning in datasets.get("warnings", []):
            print(f"WARNING: {warning}")
        export = export_training_bundle(db)
        print(f"\nExport: {export['message']}")
        print(f"Export directory: {export['exportDir']}")
        print(f"Zip bundle: {export['zipPath']}")
        for warning in export.get("warnings", []):
            print(f"WARNING: {warning}")
    print("\nTier 1 preparation complete. No model training was started.")


if __name__ == "__main__":
    main()
