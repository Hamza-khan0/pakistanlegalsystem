from app.db.session import SessionLocal
from app.services.tier1_data.importer import import_local


def main() -> None:
    with SessionLocal() as db:
        result = import_local(db)
    print(result["message"])
    for warning in result.get("warnings", []):
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    main()
