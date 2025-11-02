# Dynamic Route Planning Application

## Overview
This application provides a route optimization solution for planning efficient vehicle routes. It calculates the optimal path between start and end points while incorporating intermediate stops based on shortest distance. The system leverages OpenStreetMap (OSM) for mapping data, NetworkX for graph-based pathfinding, and Folium for interactive route visualization.

## Key Features
- **Dynamic Route Selection**: Optimize paths between user-defined start/end points and intermediate stops
- **Real-time Mapping**: Interactive map display showing the complete route with clear waypoint markers
- **Fuel Cost Estimation**: Calculate fuel consumption and costs based on user-provided efficiency and price data
- **Route Visualization**: Multi-colored path segments for improved clarity, with optional return route display
- **Interactive Map Navigation**: Click directly on map locations to set destinations and get directions

## Technologies
- **OSMnx**: Extract OpenStreetMap data and create road network graphs
- **NetworkX**: Implement pathfinding algorithms (Dijkstra's) and route optimization
- **Folium**: Render interactive maps and visualize routes
- **Geopy**: Calculate distances between geographic coordinates

## Interactive Map Functionality

### Clickable Location Points
The application includes predefined intersection points displayed as clickable markers on the map. Each intersection is identified by:
- Unique ID
- Descriptive name (e.g., "TUNA KAVŞAĞI", "ÇOCUK HASTANESİ")
- Precise coordinates (latitude and longitude)
- Area classification

Users can:
1. Click on any intersection marker to set it as a destination
2. Select multiple points to create a multi-stop route
3. View information about the selected intersection in a popup
4. Get immediate directions between any two clicked points

### Area-Based Categorization
Intersections are categorized by area type (denoted by numeric values):
- Area 5: Central city intersections
- Area 3: Suburban/peripheral intersections

This categorization helps users identify different regions and plan routes accordingly.

## Database Schema

### Users Table
| Column          | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| user_id         | INTEGER      | Primary key, auto-increment              |
| username        | VARCHAR(50)  | Unique username                          |
| email           | VARCHAR(100) | Unique email address                     |
| password_hash   | VARCHAR(255) | Hashed password                          |
| created_at      | TIMESTAMP    | Account creation time                    |
| last_login      | TIMESTAMP    | Last login time                          |
| is_active       | BOOLEAN      | Account status                           |

### Routes Table
| Column          | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| route_id        | INTEGER      | Primary key, auto-increment              |
| user_id         | INTEGER      | Foreign key to Users table               |
| name            | VARCHAR(100) | Route name                               |
| start_lat       | DECIMAL(10,7)| Starting point latitude                  |
| start_lng       | DECIMAL(10,7)| Starting point longitude                 |
| end_lat         | DECIMAL(10,7)| Ending point latitude                    |
| end_lng         | DECIMAL(10,7)| Ending point longitude                   |
| distance_km     | DECIMAL(10,2)| Total route distance in kilometers       |
| fuel_consumption| DECIMAL(10,2)| Estimated fuel consumption in liters     |
| fuel_cost       | DECIMAL(10,2)| Estimated fuel cost                      |
| created_at      | TIMESTAMP    | Route creation time                      |
| is_round_trip   | BOOLEAN      | Whether route includes return journey    |

### Waypoints Table
| Column          | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| waypoint_id     | INTEGER      | Primary key, auto-increment              |
| route_id        | INTEGER      | Foreign key to Routes table              |
| sequence        | INTEGER      | Order in the route                       |
| latitude        | DECIMAL(10,7)| Waypoint latitude                        |
| longitude       | DECIMAL(10,7)| Waypoint longitude                       |
| name            | VARCHAR(100) | Optional waypoint name/description       |

### Vehicle Profiles Table
| Column          | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| profile_id      | INTEGER      | Primary key, auto-increment              |
| user_id         | INTEGER      | Foreign key to Users table               |
| name            | VARCHAR(50)  | Profile name (e.g., "My Car")            |
| fuel_efficiency | DECIMAL(5,2) | Fuel efficiency (liters per 100km)       |
| fuel_price      | DECIMAL(6,2) | Fuel price per liter                     |
| created_at      | TIMESTAMP    | Profile creation time                    |

### Intersections Table
| Column          | Type         | Description                              |
|-----------------|--------------|------------------------------------------|
| intersection_id | INTEGER      | Primary key                              |
| intersection_name | VARCHAR(100) | Name of the intersection/location      |
| latitude        | DECIMAL(10,7)| Intersection latitude                    |
| longitude       | DECIMAL(10,7)| Intersection longitude                   |
| area            | INTEGER      | Area classification (3=suburban, 5=central) |

## Application Structure

```
route-planner/
│
├── backend/                      # Server-side code
│   ├── app/                      # Main application
│   │   ├── __init__.py           # App initialization
│   │   ├── models.py             # Database models
│   │   ├── routes.py             # API routes
│   │   ├── services/             # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py   # Authentication logic
│   │   │   ├── route_service.py  # Route calculation logic
│   │   │   └── osm_service.py    # OpenStreetMap integration
│   │   └── utils/                # Utility functions
│   │       ├── __init__.py
│   │       ├── geospatial.py     # Geospatial calculations
│   │       └── validators.py     # Input validation
│   ├── config.py                 # Configuration settings
│   ├── migrations/               # Database migrations
│   ├── tests/                    # Unit and integration tests
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # Client-side code
│   ├── public/                   # Static assets
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── assets/               # Images, fonts, etc.
│   │   ├── components/           # Reusable UI components
│   │   │   ├── Map.js            # Map visualization component
│   │   │   ├── RouteForm.js      # Route input form
│   │   │   ├── WaypointList.js   # Waypoint management
│   │   │   └── IntersectionMarker.js # Clickable map markers component
│   │   ├── pages/                # Application pages
│   │   │   ├── Dashboard.js      # User dashboard
│   │   │   ├── Login.js          # Login page
│   │   │   └── RoutePlanner.js   # Main route planning page
│   │   ├── services/             # API integration
│   │   │   └── api.js            # API client
│   │   ├── App.js                # Main app component
│   │   └── index.js              # Entry point
│   ├── package.json              # Frontend dependencies
│   └── README.md                 # Frontend documentation
│
├── docker/                       # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
│
├── .gitignore                    # Git ignore file
├── README.md                     # Project documentation
└── LICENSE                       # License information
```

## Application Flow

### 1. Input Collection
- User provides start and end coordinates (latitude and longitude)
- Optional intermediate stop coordinates can be added
- User enters fuel efficiency (liters per 100km) and fuel price
- Users can directly click on map intersections to select destinations

### 2. Graph Construction
- Application downloads relevant road network data for the specified region
- Nearest nodes in the road network are identified for all user-provided coordinates
- Intermediate stops are mapped to corresponding network nodes

### 3. Route Optimization
- Nearest Neighbor Algorithm determines the most efficient route
- Optional return trip can be calculated and optimized separately

### 4. Visualization
- Route is rendered on an interactive map using Folium
- Different line colors distinguish route segments and direction
- Clear markers indicate start, end, and intermediate waypoints
- Interactive intersection points are displayed and can be clicked for directions

### 5. Cost Calculation
- Total route distance is calculated in kilometers
- Fuel consumption and cost estimates are based on user-defined parameters

### 6. Results Display
- Interactive route map is saved as an HTML file for download
- Application summarizes key metrics: total distance, fuel consumption, and cost
