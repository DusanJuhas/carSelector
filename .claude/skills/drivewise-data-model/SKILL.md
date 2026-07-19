---
name: drivewise-data-model
description: The PostgreSQL schema and ORM/validation conventions for DriveWise AI — the cars, car_specs, car_prices, and car_features tables plus their SQLAlchemy models and Pydantic schemas. Use this whenever writing or changing anything that touches the vehicle database — models, migrations, queries, seed data, or the shape of vehicle objects returned by the API. Reach for it before defining a new table or column, writing a SQLAlchemy query, or building a Pydantic model for vehicle data, even if the task only mentions "the database" or "car data" generally.
---

# DriveWise AI — Data Model

The vehicle catalog is normalized across four PostgreSQL tables. Keep this normalization: specs, pricing, and features are separate from the core `cars` record so a car can carry many prices (per market) and many feature rows without wide sparse columns.

## Schema

```
cars
├── id            (PK)
├── brand
├── model
├── category      (a.k.a. body_type: SUV, hatchback, ...)
├── year
└── description

car_specs
├── car_id        (FK → cars.id)
├── fuel_type
├── horsepower
├── transmission
├── consumption
└── drivetrain    (FWD / RWD / AWD)

car_prices
├── car_id        (FK → cars.id)
├── market
├── price
├── currency
└── last_updated

car_features
├── car_id        (FK → cars.id)
├── feature_name
└── feature_value
```

Fields from the domain spec that map onto these tables: brand, model, year, body type (`cars.category`), seats, fuel type (`car_specs.fuel_type`), engine power (`car_specs.horsepower`), consumption (`car_specs.consumption`), trunk size, price (`car_prices`), AWD availability (`car_specs.drivetrain`). Store attributes that don't have a dedicated column (e.g. seat count, trunk capacity) as `car_features` rows so the model stays extensible.

## Conventions

- Use **SQLAlchemy** models — one class per table, relationships declared with `relationship()` and matching foreign keys. A `Car` has many `CarSpec`, `CarPrice`, and `CarFeature` (typically one spec row, many prices/features).
- Use **Pydantic** schemas for API I/O — never return raw ORM objects. Keep separate `...Create`, `...Read`, and internal schemas; the `Read` schema is what the API contract exposes.
- Pydantic schema shapes must match `docs/api-contract.md`. If you change a vehicle field, update the contract in the same change.
- `car_prices.last_updated` is set by the scraper — treat it as write-owned by the data-collection layer, read-only elsewhere.
- Money: store `price` + `currency` together; never assume a single currency. Filter/compare in the recommendation engine, not by hardcoding conversions here.

## Query guidance

- The recommendation engine reads candidate vehicles from here; expose query helpers that filter by the structured parameters the AI layer produces (min_seats, body_type, budget, fuel_type, drivetrain, etc.) rather than scattering raw queries across the codebase.
- Join specs/prices/features eagerly when returning a full vehicle detail; keep list/search queries lean.

## Example vehicle (denormalized view)

```json
{
  "brand": "Skoda",
  "model": "Kodiaq",
  "seats": 7,
  "fuel_type": "Diesel",
  "body_type": "SUV",
  "trunk_capacity": 835,
  "drivetrain": "AWD"
}
```
