[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/crowdbotics-research-projects/context-cohort-02)

# Magazine Subscription Service

This project is a backend service built using FastAPI for managing magazine subscriptions. The service exposes a REST API that allows users to:

1. Register, login, and reset their passwords.
2. Retrieve a list of magazines available for subscription, including plans and discounts.
3. Create subscriptions for magazines.
4. Retrieve, modify, and delete their subscriptions.

## Features

- User authentication and password management.
- Magazine and subscription management.
- Support for multiple subscription plans with varying renewal periods and discounts.
- Business rules for modifying and deactivating subscriptions.

## Data Models

### Magazine

Represents a magazine available for subscription. Each magazine includes:

- `name`: The name of the magazine.
- `description`: A brief description of the magazine.
- `base_price`: The monthly subscription price (must be greater than zero).

### Plan

Represents subscription plans with the following properties:

- `title`: The name of the plan.
- `description`: A description of the plan.
- `renewalPeriod`: The number of months for the subscription renewal (must be greater than zero).
- `tier`: A numerical value representing the plan's level (higher tiers are more expensive).
- `discount`: A percentage discount for the plan (e.g., 0.1 for 10%).

#### Supported Plans

1. **Silver Plan**
   - Renewal Period: 1 month
   - Tier: 1
   - Discount: 0.0 (no discount)

2. **Gold Plan**
   - Renewal Period: 3 months
   - Tier: 2
   - Discount: 5% (0.05)

3. **Platinum Plan**
   - Renewal Period: 6 months
   - Tier: 3
   - Discount: 10% (0.10)

4. **Diamond Plan**
   - Renewal Period: 12 months
   - Tier: 4
   - Discount: 25% (0.25)

### Subscription

Tracks the relationship between a user, a magazine, and a plan. Each subscription includes:

- `user_id`: The ID of the user.
- `magazine_id`: The ID of the magazine.
- `plan_id`: The ID of the plan.
- `price`: The price at renewal (calculated as `base_price` minus the plan's discount).
- `renewal_date`: The next renewal date.
- `is_active`: Indicates whether the subscription is active.

**Note:** Subscriptions are never deleted. Instead, inactive subscriptions are marked with `is_active = False` and excluded from user queries.

## Business Rules

1. Users can modify subscriptions before the renewal period ends. Modifications deactivate the current subscription and create a new one with the updated plan and renewal date.
2. No proration or refunds are issued for subscription modifications.
3. Users can only have one active subscription per magazine and plan at a time.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- PostgreSQL database
- Docker (optional for containerized development)

### Installation

1. Clone the repository:

   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Set up the database by applying migrations:

   ```sh
   alembic upgrade head
   ```

### Running the Application

#### Using FastAPI Development Server

Run the application locally:

```sh
uvicorn app.main:app --reload
```

#### Using Docker Compose

Alternatively, start the application using Docker Compose:

```sh
docker-compose up --build
```

### API Documentation

Once the application is running, access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite using Pytest:

```sh
pytest
```

## License

This project is licensed under the MIT License.
