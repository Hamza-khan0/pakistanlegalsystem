from app.db.session import SessionLocal
from app.services.tier1_data.dataset_builder import build_tier1_datasets


def main() -> None:
    with SessionLocal() as db:
        result = build_tier1_datasets(db)
    print(result["message"])
    for item in result["datasets"]:
        print(f"{item['taskName']}: {item['recordCount']} records")
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
