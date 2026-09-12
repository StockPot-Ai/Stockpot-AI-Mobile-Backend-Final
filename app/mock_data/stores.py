"""Mock stores dataset containing 4 major supermarket chains in Sri Lanka."""

MOCK_STORES = [
    {
        "id": "33333333-0000-0000-0000-000000000001",
        "name": "Cargills",
        "latitude": 6.8965,
        "longitude": 79.8562,
        "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5a/Cargills_Ceylon_logo.svg/300px-Cargills_Ceylon_logo.svg.png"
    },
    {
        "id": "33333333-0000-0000-0000-000000000002",
        "name": "Keells",
        "latitude": 6.9080,
        "longitude": 79.8660,
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Keells_Super_Logo.svg/320px-Keells_Super_Logo.svg.png"
    },
    {
        "id": "33333333-0000-0000-0000-000000000003",
        "name": "Glomark",
        "latitude": 6.9033,
        "longitude": 79.8519,
        "logo_url": "https://softlogicglomark.com/images/glomark_logo.png"
    },
    {
        "id": "33333333-0000-0000-0000-000000000004",
        "name": "Local Market",
        "latitude": 6.9360,
        "longitude": 79.8570,
        "logo_url": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=200&q=80"
    }
]

STORE_BY_ID = {store["id"]: store for store in MOCK_STORES}
STORE_BY_NAME = {store["name"].lower(): store for store in MOCK_STORES}
