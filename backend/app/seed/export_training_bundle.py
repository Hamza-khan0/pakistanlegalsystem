from app.db.session import SessionLocal
from app.services.tier1_data.export_bundle import export_training_bundle


def main() -> None:
    with SessionLocal() as db:
        result = export_training_bundle(db)
    print(result["message"])
    print(f"Export directory: {result['exportDir']}")
    print(f"Zip bundle: {result['zipPath']}")
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
