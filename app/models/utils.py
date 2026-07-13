def serialize_document(document: dict) -> dict:
    """Convert a MongoDB document's `_id` (ObjectId) into a string `id` field."""
    if document is None:
        return None
    data = dict(document)
    data["id"] = str(data.pop("_id"))
    return data


def serialize_documents(documents: list[dict]) -> list[dict]:
    return [serialize_document(doc) for doc in documents]